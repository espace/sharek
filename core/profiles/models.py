from django.db import models
from django.contrib.auth.models import User
from core.models import ArticleDetails
from django.db import connection, models
from django import db

@classmethod
def profile_likes(self, user):
       return profile_likes_dislikes(self, user, True)
#   SELECT DISTINCT ON (core_topic.id, core_topic.name) core_topic.name, core_topic.id, core_topic.slug, core_suggestion.description, core_articledetails.mod_date
#FROM core_topic
#INNER JOIN core_articleheader ON core_articleheader.topic_id = core_topic.id
#INNER JOIN core_articledetails ON core_articledetails.header_id = core_articleheader.id
#INNER JOIN core_suggestion ON core_suggestion.articledetails_id = core_articledetails.id
#
#INNER JOIN core_suggestionvotes ON core_suggestionvotes.suggestions_id = core_suggestion.id
#AND core_suggestionvotes.user = 'admin' AND core_suggestionvotes.vote IS true
#
#WHERE core_articledetails.current IS TRUE
#ORDER BY core_topic.id DESC limit 3




@classmethod
def profile_dislikes(self, user):
       return profile_likes_dislikes(self, user, False)

def profile_likes_dislikes(self, user, is_likes):
       query = '''SELECT core_articleheader.topic_id, core_articleheader.name, core_topic.slug, core_articleheader.order,
					core_articledetails.id, core_articledetails.header_id, core_articledetails.slug, core_articledetails.summary, core_articledetails._summary_rendered,
					core_articledetails.likes, core_articledetails.dislikes, core_articledetails.mod_date, core_articledetails.feedback_count,
					core_articleheader.chapter_id, core_chapter.name, core_articleheader.branch_id, core_branch.name, core_topic.name,
					core_branch.slug, core_chapter.slug, core_articledetails.original, original_articledetails.slug
				FROM core_articleheader
				INNER JOIN core_articledetails ON core_articleheader.id = core_articledetails.header_id
				INNER JOIN core_articlerating ON core_articledetails.id = core_articlerating.articledetails_id
					AND core_articlerating.user = %s AND core_articlerating.vote IS %s
				INNER JOIN core_articledetails original_articledetails ON original_articledetails.id = core_articledetails.original
				INNER JOIN core_topic ON core_articleheader.topic_id = core_topic.id
				LEFT JOIN core_chapter ON core_articleheader.chapter_id = core_chapter.id
				LEFT JOIN core_branch ON core_articleheader.branch_id = core_branch.id
				WHERE core_articledetails.current IS TRUE
				ORDER BY coalesce(core_topic.order, 0), coalesce(core_chapter.order, 0), coalesce(core_branch.order, 0), core_articleheader.order'''

       cursor = connection.cursor()
       cursor.execute(query, [user, is_likes])

       articles_list = []

       for row in cursor.fetchall():
           p = ArticleDetails(id=row[4], header_id=row[5], slug=row[6], summary=row[7], _summary_rendered=row[8], likes=row[9], dislikes=row[10], mod_date=row[11], feedback_count=row[12], original=row[20])
           p.topic_id = row[0]
           p.name = row[1]
           p.topic_slug = row[2]
           p.order = row[3]
           p.chapter_id = row[13]
           p.chapter_name = row[14]
           p.branch_id = row[15]
           p.branch_name = row[16]
           p.topic_name = row[17]
           p.branch_slug = row[18]
           p.chapter_slug = row[19]
           p.original_slug = row[21]
           articles_list.append(p)

       cursor.close()
       return articles_list

User.add_to_class('profile_likes', profile_likes)
User.add_to_class('profile_dislikes', profile_dislikes)
