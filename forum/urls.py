# forum/urls.py
from django.urls import path
from . import views

app_name = "forum"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("create/", views.create_post, name="create_post"),
    path("<int:post_id>/upvote/", views.upvote, name="upvote"),
    path("<int:post_id>/downvote/", views.downvote, name="downvote"),
    path("<int:post_id>/delete/", views.delete_post, name="delete_post"),  # <- ini
    path("<int:post_id>/edit/", views.edit_post, name="edit_post"),

    path("<int:post_id>/comments/", views.comment_list, name="comment_list"),
    path("<int:post_id>/comments/add/", views.comment_add, name="comment_add"),

    path("json/", views.post_list_json, name="post_list_json"),
    path("json/create/", views.create_post_json, name="create_post_json"),
    path("json/<int:post_id>/upvote/", views.upvote_json, name="upvote_json"),
    path("json/<int:post_id>/downvote/", views.downvote_json, name="downvote_json"),
    path("json/<int:post_id>/delete/", views.delete_post_json, name="delete_post_json"),
    path("json/<int:post_id>/edit/", views.edit_post_json, name="edit_post_json"),

    path("json/<int:post_id>/comments/", views.comment_list_json, name="comment_list_json"),
    path("json/<int:post_id>/comments/add/", views.comment_add_json, name="comment_add_json"),
]
