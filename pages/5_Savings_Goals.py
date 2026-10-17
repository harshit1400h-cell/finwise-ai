from datetime import date

import streamlit as st

from src.database import init_db
from src.goals import add_goal, delete_goal, get_goals, update_goal_progress

init_db()
st.title("🌱 Savings Goals")
st.caption("Track only the amounts you explicitly record. Future contributions are estimates.")

with st.expander("Create a savings goal", expanded=not bool(get_goals())):
    with st.form("create_goal"):
        name = st.text_input("Goal name")
        target = st.number_input("Target amount (₹)", min_value=0.01, step=500.0)
        saved = st.number_input("Already saved (₹)", min_value=0.0, step=100.0)
        target_date = st.date_input("Target date", value=date.today().replace(year=date.today().year + 1))
        description = st.text_area("Description (optional)")
        submit = st.form_submit_button("Create goal", type="primary")
    if submit:
        try:
            add_goal(name, target, saved, target_date.isoformat(), description)
            st.success("Savings goal created.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))
        except Exception:
            st.error("Could not create the goal. Check the local database.")

goals = get_goals()
if not goals:
    st.info("Create a goal to track progress and estimate a contribution plan.")
for goal in goals:
    with st.container(border=True):
        st.subheader(goal["name"])
        st.write(goal["description"] or "No description")
        st.progress(min(max(goal["progress"], 0), 1),
                    text=f"₹{goal['saved']:,.2f} saved of ₹{goal['target']:,.2f} "
                         f"({goal['progress']:.0%})")
        if goal["remaining"] > 0:
            if goal["overdue"]:
                st.warning(f"Target date {goal['target_date']} has passed. Choose a new date "
                           "to make a useful contribution estimate.")
            else:
                st.write(f"₹{goal['remaining']:,.2f} remaining · estimated ₹"
                         f"{goal['monthly_contribution']:,.2f} per month to target "
                         f"{goal['target_date']}")
        else:
            st.success("Goal reached!")
        with st.form(f"progress_{goal['id']}"):
            new_saved = st.number_input("Update saved amount (₹)", min_value=0.0,
                max_value=goal["target"], value=goal["saved"], step=100.0,
                key=f"saved_{goal['id']}")
            update = st.form_submit_button("Update progress")
        if update:
            try:
                update_goal_progress(goal["id"], new_saved)
                st.success("Progress updated.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
        if st.checkbox("Confirm goal deletion", key=f"confirm_goal_{goal['id']}"):
            if st.button("Delete goal", key=f"delete_goal_{goal['id']}"):
                try:
                    delete_goal(goal["id"])
                    st.success("Goal deleted.")
                    st.rerun()
                except Exception:
                    st.error("Could not delete this goal.")
