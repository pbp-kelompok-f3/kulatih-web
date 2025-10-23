from django.urls import path
from . import views
app_name = "forum"
urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("create/", views.create_post, name="create_post"),
    path("<int:post_id>/upvote/", views.upvote, name="upvote"),
    path("<int:post_id>/downvote/", views.downvote, name="downvote"),
    path("<int:post_id>/delete/", views.delete_post, name="delete_post"),
]
