from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("coach/<uuid:coach_id>/", views.coach_reviews_json, name="coach_reviews_json"),
    path("coach/<uuid:coach_id>/create/", views.create_review_json, name="create_review_json"),
    path("detail/<int:review_id>/", views.review_detail_json, name="review_detail_json"),
    path("update/<int:review_id>/", views.update_review_json, name="update_review_json"),
    path("delete/<int:review_id>/", views.delete_review_json, name="delete_review_json"),
    path("page/<int:review_id>/", views.review_detail_page, name="review_detail_page"),
]
