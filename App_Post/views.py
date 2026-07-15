from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from App_Post.filters import PostFilter
from App_Post.models import Comment, Post, Reply, SubSubject, Subject


@login_required
def add_comment(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id)
        content = request.POST.get('content', '').strip()

        if content:
            comment = Comment.objects.create(
                post=post, 
                user=request.user, 
                content=content
            )
            return render(request, 'partials/comment.html', {'comment': comment})

    return HttpResponse(status=400)

@login_required
def add_reply(request, comment_id, reply_id=None):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if request.method == "GET":
        # Render the reply form for the specific comment or reply
        if reply_id:
            reply = get_object_or_404(Reply, id=reply_id)
            return render(request, 'partials/reply_form.html', {'comment': comment,
                                                                        'reply': reply})
        return render(request, 'partials/reply_form.html', {'comment': comment})

    elif request.method == "POST":
        content = request.POST.get('content', '').strip()
        if content:
            reply = Reply.objects.create(
                comment=comment,
                user=request.user,
                content=content,
            )
            return render(request, 'partials/comment.html', {'comment': reply})

    return HttpResponse(status=400)

def post_all(request, slug_subject=None, slug_subsubject=None):
    current_subject = None
    current_subsubject = None

    # Lọc bài viết theo Subject và SubSubject
    if slug_subject and slug_subsubject: # posts thuộc SubSubject
        current_subject = get_object_or_404(Subject, slug=slug_subject)
        current_subsubject = get_object_or_404(
            SubSubject,
            subject=current_subject,
            slug=slug_subsubject,
        )
        posts = Post.objects.filter(
            subject=current_subject,
            subsubject=current_subsubject,
        ).order_by('-display_at')
    elif slug_subject: # posts thuộc Subject
        current_subject = get_object_or_404(Subject, slug=slug_subject)
        posts = Post.objects.filter(subject=current_subject).order_by('-display_at')
    else: # tất cả posts
        posts = Post.objects.all().order_by('-display_at')
        
    # Số lượng bài viết trước khi lọc
    total_posts = posts.count()
    
    subject_filters = [
        int(subject_id)
        for subject_id in request.GET.getlist('subject')
        if str(subject_id).isdigit()
    ]
    if current_subject and not subject_filters:
        subject_filters = [current_subject.id]
    keyword_filter = request.GET.get('keyword')
    # print(subject_filters)
    # print(keyword_filter)
    
    if subject_filters:
        posts = posts.filter(subject__id__in=subject_filters)
    if keyword_filter:
        posts = posts.filter(Q(title__icontains=keyword_filter) | Q(description__icontains=keyword_filter))

    # Số lượng bài viết sau khi lọc
    filtered_posts_count = posts.count()
    
    # Phân trang
    paginator = Paginator(posts, 12) # 12 posts per page
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    # Chuẩn bị context
    context = {
        'posts': posts,
        'subject': current_subject,
        'subsubject': current_subsubject,
        'total_posts': total_posts,  # Tổng số bài viết
        'filtered_posts_count': filtered_posts_count,  # Số bài viết sau khi lọc
        'subjects': Subject.objects.all().order_by('id'),  # khớp thứ tự navbar/trang chủ (context processor)
        'selected_subjects': subject_filters,
        'keyword': keyword_filter,
        
        'target_content_id': '#post-content',
        'include_form_filter_id': '#post-filter-form',
    }
    
    # Xử lý yêu cầu HTMX nếu có
    if request.headers.get('HX-Request'):
        return render(request, 'partials/posts_pagination.html', context)

    return render(request, 'post_all.html', context)

def post_detail(request, slug_subject, slug_post):
    post = get_object_or_404(Post, slug=slug_post)
    postphotos = post.photo_post.all()
    related_posts = Post.objects.filter(subject=post.subject).exclude(slug=slug_post)[0:3]

    # Get the previous post based on created_at
    previous_post = Post.objects.filter(subject=post.subject, created_at__lt=post.created_at).order_by('-created_at').first()
    # Get the next post based on created_at
    next_post = Post.objects.filter(subject=post.subject, created_at__gt=post.created_at).order_by('created_at').first()

    # Get top-level comments (those without a parent)
    # top_level_comments = post.comments.filter(parent__isnull=True)

    subject = post.subject
    subjects = Subject.objects.all()

    return render(request, 'post_detail.html', {'post': post,
                                                        'postphotos':postphotos,
                                                        'related_posts':related_posts,
                                                        
                                                        'previous_post': previous_post,
                                                        'next_post': next_post,
                                                        
                                                        # 'top_level_comments': top_level_comments,  # Pass top-level comments to the template
                                                        
                                                        'subject':subject,
                                                        'subjects':subjects,})

def subject(request, slug_subject):
    subject = get_object_or_404(Subject, slug=slug_subject) # lọc 1 subject, rồi từ subject vừa lọc, tìm các posts của nó
    posts = subject.posts.all()
    
    queryset = Post.objects.all()
    filterset = PostFilter(request.GET, queryset=queryset)

    return render(request, 'post_all.html', {'subject':subject,
                                                    'posts':posts,
                                                    
                                                    'filter': filterset,})

def subsubject(request, slug_subsubject):
    subsubject = get_object_or_404(SubSubject, slug=slug_subsubject) # lọc 1 subsubject, rồi từ subsubject vừa lọc, tìm các posts của nó
    posts = subsubject.posts.all()
    
    queryset = Post.objects.all()
    filterset = PostFilter(request.GET, queryset=queryset)

    return render(request, 'post_all.html', {'subsubject':subsubject,
                                                    'posts':posts,
                                                    
                                                    'filter': filterset,})

