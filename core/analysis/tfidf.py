from core.models import Feedback
import core.analysis.preprocessing as pre

def compute_idf():
  query ='''SELECT distinct articledetails_id from core_feedback order by 1'''
  cursor = connection.cursor()
  cursor.execute(query)
  ids = cursor.fetchall()

  for id in ids:
    query = '''SELECT distinct suggestion from core_feedback where parent_id is NULL and articledetails_id = %s'''
    cursor = connection.cursor()
    cursor.execute(query, [id[0]])
    suggestions = cursor.fetchall()
    pre.stammer(suggestions)


