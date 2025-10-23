from django.urls import path
from . import views

app_name = "reviews"
urlpatterns = [
    path("coach/<int:coach_id>/", views.coach_reviews_json, name="coach_reviews_json"),
    path("coach/<int:coach_id>/create/", views.create_review_json, name="create_review_json"),
    path("delete/<int:review_id>/", views.delete_review_json, name="delete_review_json"),  
    path("update/<int:review_id>/", views.update_review_json, name="update_review_json"),  
]
