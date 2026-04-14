# # history.py — UPGRADE 3: View saved analysis history

# # from flask import Blueprint, render_template, jsonify
# # from flask_login import login_required, current_user

# # history_bp = Blueprint('history', __name__)


# # @history_bp.route('/')
# # @login_required
# # def view_history():
# #     """Show all past analyses for the logged-in user."""
# #     try:
# #         from app.models.database import AnalysisResult, RankingSession
# #         analyses = (AnalysisResult.query
# #                     .filter_by(user_id=current_user.id)
# #                     .order_by(AnalysisResult.created_at.desc())
# #                     .limit(50).all())
# #         rankings = (RankingSession.query
# #                     .filter_by(user_id=current_user.id)
# #                     .order_by(RankingSession.created_at.desc())
# #                     .limit(20).all())
# #         return render_template('history.html', analyses=analyses, rankings=rankings)
# #     except Exception as e:
# #         return render_template('history.html', analyses=[], rankings=[], error=str(e))


# # @history_bp.route('/api/stats')
# # @login_required
# # def api_stats():
# #     """JSON endpoint: user's score stats over time (for chart)."""
# #     try:
# #         from app.models.database import AnalysisResult
# #         results = (AnalysisResult.query
# #                    .filter_by(user_id=current_user.id)
# #                    .order_by(AnalysisResult.created_at.asc())
# #                    .all())
# #         return jsonify({
# #             'labels': [r.created_at.strftime('%d %b') for r in results],
# #             'overall': [r.overall_score for r in results],
# #             'skills':  [r.skills_score  for r in results],
# #             'ats':     [r.ats_score     for r in results],
# #         })
# #     except Exception as e:
# #         return jsonify({'error': str(e)}), 500





# from flask import Blueprint, render_template, jsonify
# from flask_login import login_required, current_user

# history_bp = Blueprint("history", __name__)


# @history_bp.route("/")
# @login_required
# def view_history():
#     try:
#         from app.models.database import AnalysisResult, RankingSession

#         analyses = (
#             AnalysisResult.query
#             .filter_by(user_id=current_user.id)
#             .order_by(AnalysisResult.created_at.desc())
#             .limit(50)
#             .all()
#         )

#         rankings = (
#             RankingSession.query
#             .filter_by(user_id=current_user.id)
#             .order_by(RankingSession.created_at.desc())
#             .limit(20)
#             .all()
#         )

#         return render_template("history.html", analyses=analyses, rankings=rankings)
#     except Exception as e:
#         return render_template("history.html", analyses=[], rankings=[], error=str(e))


# @history_bp.route("/api/stats")
# @login_required
# def api_stats():
#     try:
#         from app.models.database import AnalysisResult

#         results = (
#             AnalysisResult.query
#             .filter_by(user_id=current_user.id)
#             .order_by(AnalysisResult.created_at.asc())
#             .all()
#         )

#         return jsonify({
#             "labels": [r.created_at.strftime("%d %b") for r in results],
#             "overall": [r.overall_score for r in results],
#             "skills": [r.skills_score for r in results],
#             "ats": [r.ats_score for r in results],
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

history_bp = Blueprint("history", __name__)


@history_bp.route("/")
@login_required
def view_history():
    try:
        from app.models.database import AnalysisResult, RankingSession

        analyses = (
            AnalysisResult.query
            .filter_by(user_id=current_user.id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(50)
            .all()
        )

        rankings = (
            RankingSession.query
            .filter_by(user_id=current_user.id)
            .order_by(RankingSession.created_at.desc())
            .limit(20)
            .all()
        )

        return render_template(
            "history.html",
            records=analyses,          # Claude's fix: template expects records
            rankings=rankings,
            user_name=current_user.name,
            total_count=len(analyses)
        )

    except Exception as e:
        return render_template(
            "history.html",
            records=[],
            rankings=[],
            user_name=getattr(current_user, "name", "User"),
            total_count=0,
            error=str(e)
        )


@history_bp.route("/api/stats")
@login_required
def api_stats():
    try:
        from app.models.database import AnalysisResult

        results = (
            AnalysisResult.query
            .filter_by(user_id=current_user.id)
            .order_by(AnalysisResult.created_at.asc())
            .all()
        )

        return jsonify({
            "labels": [r.created_at.strftime("%d %b") for r in results],
            "overall": [r.overall_score for r in results],
            "skills": [r.skills_score for r in results],
            "ats": [r.ats_score for r in results],
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500