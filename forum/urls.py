from django.urls import path
from . import views

app_name = "forum"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("create/", views.create_post, name="create_post"),
    path("<int:post_id>/upvote/", views.upvote, name="upvote"),
    path("<int:post_id>/downvote/", views.downvote, name="downvote"),
    path("<int:post_id>/delete/", views.delete_post, name="delete_post"),
    path("<int:post_id>/edit/", views.edit_post, name="edit_post"),

    # comments API (AJAX)
    path("<int:post_id>/comments/", views.comment_list, name="comment_list"),                  # GET
    path("<int:post_id>/comments/add/", views.comment_add, name="comment_add"),                # POST
    path("<int:post_id>/comments/<int:comment_id>/edit/", views.comment_edit, name="comment_edit"),  # POST  <-- NEW
    path("<int:post_id>/comments/<int:comment_id>/delete/", views.comment_delete, name="comment_delete"),  # POST
    path("<int:post_id>/comments/<int:comment_id>/vote/<str:action>/", views.comment_vote, name="comment_vote"),  # POST (unused for replies now)
]
