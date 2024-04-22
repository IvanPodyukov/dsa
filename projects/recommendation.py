import hashlib
import pickle

import pandas as pd
from django.db.models import Value, When, Case, FloatField
from surprise import Reader, Dataset, SVD

from projects.models import Rating, Project

from django.core.cache import cache


def recommend_projects(user):
    ratings = Rating.objects.all()
    data_hash = hashlib.md5(pickle.dumps(list(ratings))).hexdigest()
    cached_data = cache.get('data_hash')
    cached_model = cache.get('recommendation_model')
    train_set = prepare_trainset(ratings)
    if cached_data == data_hash and cached_model:
        model = cached_model
    else:
        model = train_model(train_set)
        cache.set("recommendation_model", model)
        cache.set("data_hash", data_hash)
    pred = predict_ratings(model, train_set, user)
    return get_projects_queryset(pred)


def prepare_trainset(ratings):
    ratings_df = pd.DataFrame(list(ratings.values()), columns=['user_id', 'project_id', 'rating'])
    reader = Reader(rating_scale=(0, 5))
    data = Dataset.load_from_df(ratings_df, reader)
    train_set = data.build_full_trainset()
    return train_set


def train_model(train_set):
    svd = SVD()
    svd.fit(train_set)
    return svd


def predict_ratings(svd, train_set, user):
    # anti_testset_user = get_anti_testset_user(train_set, user)
    anti_testset = train_set.build_anti_testset()
    predictions = svd.test(anti_testset)
    pred = pd.DataFrame(predictions)
    if 'uid' not in pred:
        return pred
    return pred[pred['uid'] == user]


'''
def get_anti_testset_user(train_set, user):
    anti_testset_user = []
    fill_value = train_set.global_mean
    user_item_ratings = train_set.ur[user]
    user_items = [item for (item, _) in user_item_ratings]
    for iid in train_set.all_items():
        if iid not in user_items:
            anti_testset_user.append((train_set.to_raw_uid(user - 1), train_set.to_raw_iid(iid), fill_value))
    return anti_testset_user
'''


def get_projects_queryset(pred):
    if 'iid' not in pred:
        return Project.objects.none()
    projects = Project.objects.filter(pk__in=pred['iid'])
    ratings = {}
    for x in pred[['iid', 'est']].to_dict('records'):
        ratings[x['iid']] = x['est']
    conditions = [When(id=key, then=Value(value)) for key, value in ratings.items()]
    return projects.annotate(expected_rating=Case(
        *conditions,
        default=Value(None),
        output_field=FloatField()
    )).filter(expected_rating__gt=3.5).order_by('-expected_rating')
