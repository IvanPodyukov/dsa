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
    if cached_data == data_hash and cached_model is not None:
        model = cached_model
    else:
        model = train_model(train_set)
    pred = predict_ratings(model, train_set, user)
    cache.set("data_hash", data_hash)
    cache.set("recommendation_model", model)
    return get_projects_queryset(pd.DataFrame(pred))


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


def predict_ratings(model, train_set, user):
    anti_testset_user = [(uid, iid, r_ui) for uid, iid, r_ui in train_set.build_anti_testset() if uid == user]
    predictions = model.test(anti_testset_user)
    pred = pd.DataFrame(predictions)
    return pred


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
    )).order_by('-expected_rating')
