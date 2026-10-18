try:
    from . import auth, students, teachers, classes, assignments, submissions, scores, attendance, leaderboard, dashboard
except ImportError:
    from app.api import auth, students, teachers, classes, assignments, submissions, scores, attendance, leaderboard, dashboard
