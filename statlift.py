import streamlit as st
import pandas as pd
import altair as alt
from os.path import join, dirname
from session_state_handler import init_session_state_updates, on_csv_upload, \
    on_date_change, on_exercise_change, on_workout_change
from sepump import SePump
from streamlit_utils import v_space

def show_total_stats(data: pd.DataFrame) -> None:
    """Shows aggregated metrics across all workouts and exercises in data.

    Args:
        data (pd.DataFrame): Pandas dataframe containing workout data.
    """
    total_workouts = len(pd.unique(data["workout_uid"]))
    total_sets = len(data[st.session_state["columns"]["REPS"]])
    total_reps = sum(data[st.session_state["columns"]["REPS"]])
    total_volume = sum(data["volume"])
    duration_data = data.groupby("workout_uid").agg(**{
        "duration": (st.session_state["columns"]["WORKOUT_DURATION"], "first")
    })
    total_duration = duration_data["duration"].fillna(0).sum()
    cl1, cl2, cl3, cl4, cl5 = st.columns(5)
    cl1.metric(label="\# of Workouts", value="{:,}".format(int(total_workouts)))
    cl2.metric(label="Total Volume (kg)", value="{:,}".format(int(total_volume)))
    cl3.metric(label="\# of Sets", value="{:,}".format(int(total_sets)))
    cl4.metric(label="\# of Reps", value="{:,}".format(int(total_reps)))
    cl5.metric(label="\# of Minutes trained", value="{:,}".format(int(total_duration)))


if __name__ == "__main__":
    # setup page
    st.set_page_config(
        page_title="LiftWise",
        page_icon=":mechanical_arm",
        layout="wide"
    )
    st.title("LiftWise (Beta) - Free Analytics for Hevy Data :rocket:")

    # Google Analytics
    GA_TRACKING_ID = st.secrets["google_analytics"]["GA_TRACKING_ID"]
    
    # Create the GA tracking code using streamlit's built-in components
    ga_script = f"""
        <script>
            // Create a new script element
            var script = document.createElement('script');
            script.src = 'https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}';
            script.async = true;
            document.head.appendChild(script);
            
            // Initialize dataLayer and gtag function
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{GA_TRACKING_ID}');
        </script>
    """
    
    # Inject the script using a custom component
    st.components.v1.html(ga_script, height=0)

    # initialize workout data handler
    sepump = SePump()

    # load csv file
    st.write("## :page_facing_up: Upload csv file (exported from Hevy-App):")
    csv = st.file_uploader("_", label_visibility="hidden", on_change=on_csv_upload)

    # # don't calculate / render rest of the page if no csv is provided
    if csv is None:
        exit()
    
    # load & clean data and save it in streamlit session state
    if st.session_state["updated_csv"]:
        sepump.load_data(csv)
        columns_path = join(dirname(__file__), "columns.json")
        try:
            sepump.load_column_names(columns_path)
        except Exception:
            st.error("Seems like your file is not supported by LiftWise")
            exit()
        sepump.clean_data()
        st.session_state["cleaned_data"] = sepump.data
        st.session_state["data"] = sepump.data
        st.session_state["columns"] = sepump.columns
        st.session_state["start_date"] = sepump.data[st.session_state["columns"]["DATE"]].min()
        st.session_state["end_date"] = sepump.data[st.session_state["columns"]["DATE"]].max()
    else:
        sepump.data = st.session_state["data"]
        sepump.columns = st.session_state["columns"]

    st.divider()
    
    # set date range
    st.write("## :date: Select date range:")
    fl1, fl2 = st.columns(2)
    start_date_filter = fl1.date_input(
        "**Start date**", 
        st.session_state["start_date"],
        on_change=on_date_change
    )
    end_date_filter = fl2.date_input(
        "**End date**",
        st.session_state["end_date"],
        on_change=on_date_change
    )
    
    if st.session_state["updated_date"]:
        sepump.data = st.session_state["cleaned_data"]
        sepump.update_date_range(start_date_filter, end_date_filter)
        st.session_state["data"] = sepump.data
        st.session_state["columns"] = sepump.columns
    
    # don't calculate / render rest of the page if there are no workouts in 
    # specified date range
    if len(st.session_state["data"]) == 0:
        exit()

    ###########################################################################
    # 1. Overall metrics of workouts in date range
    ###########################################################################

    st.divider()
    st.write("## :bar_chart: Metrics across all workouts:")
    show_total_stats(st.session_state["data"])

    ###########################################################################
    # 2. Metrics and graphs for individual exercises
    ###########################################################################

    st.divider()
    st.write("## :mechanical_arm: Metrics for individual exercises:")

    exercise_filter = st.selectbox(
        "**Select exercise**",
        pd.unique(st.session_state["data"][st.session_state["columns"]["EXERCISE_NAME"]]),
        on_change=on_exercise_change
    )

    if st.session_state["updated_exercise"]:
        sepump.update_exercise_data(exercise_filter)
        st.session_state["exercise_data"] = sepump.exercise_data
        st.session_state["previous_exercise_data"] = sepump.prev_exercise_data
    else:
        sepump.exercise_data = st.session_state["exercise_data"]
        sepump.prev_exercise_data = st.session_state["previous_exercise_data"]

    # 2a. Metrics
    v_space(1)
    st.write(f"##### :bar_chart: Metrics for *{exercise_filter}*:")
    
    total_sets, total_sets_delta = sepump.calculate_exercise_metric_and_delta("date", "len")
    total_reps, total_reps_delta = sepump.calculate_exercise_metric_and_delta("total_reps", "sum")
    total_volume, total_volume_delta = sepump.calculate_exercise_metric_and_delta("total_volume", "sum")
    max_weight, max_weight_delta = sepump.calculate_exercise_metric_and_delta("max_weight", "max")
    max_reps, max_reps_delta = sepump.calculate_exercise_metric_and_delta("max_reps", "max")
    max_volume, max_volume_delta = sepump.calculate_exercise_metric_and_delta("max_volume", "max")

    ecl1, ecl2, ecl3 = st.columns(3)
    ecl1.metric(label="Total Sets", value=total_sets, delta=total_sets_delta)
    ecl2.metric(label="Total Reps", value=total_reps, delta=total_reps_delta)
    ecl3.metric(label="Total Volume (kg)", value=total_volume, delta=total_volume_delta)
    ecl1.metric(label="Max Weight (kg)", value=max_weight, delta=max_weight_delta)
    ecl2.metric(label="Max Reps", value=max_reps, delta=max_reps_delta)
    ecl3.metric(label="Max Volume (kg)", value=max_volume, delta=max_volume_delta)

    # 2b. Graphs
    v_space(1)
    st.write(f"##### :chart_with_upwards_trend: Graphs for *{exercise_filter}*:")

    metric_to_column = {
        "Total Volume (per workout)": "total_volume",
        "Mean Weight (across sets per workout)": "mean_weight",
        "Mean Reps (across sets per workout)": "mean_reps",
        "Max Weight (across sets per workout)": "max_weight",
        "Max Reps (across sets per workout)": "max_reps",
        "Max Volume (across sets per workout)": "max_volume",
    }
    selected_metrics = st.multiselect(
        "**Select metrics to plot**", 
        metric_to_column.keys(),
        default=metric_to_column.keys()
    )
    graph_columns = st.columns(2)

    for m, metric in enumerate(selected_metrics):
        col_index = m % 2
        col = graph_columns[col_index]
        chart = alt.Chart(
            sepump.exercise_data, title=f"{metric} for {exercise_filter}"
        ).mark_line(point=True).encode(
            x=alt.X("date", title="Date"),
            y=alt.Y(metric_to_column[metric], title=metric),
            tooltip=[
                alt.Tooltip("date", title="Date"),
                alt.Tooltip(metric_to_column[metric], title=metric),
                alt.Tooltip("notes", title="Notes")
            ]
        )
        chart += chart.transform_regression('date', metric_to_column[metric]).mark_line(color="red")
        col.altair_chart(chart, use_container_width=True)
    
    ###########################################################################
    # 3. Metrics and graphs for individual workout routines (e.g. pull day)
    ###########################################################################

    st.divider()
    st.write("## :repeat: Metrics for individual workout routines:")
    workout_filter = st.selectbox(
        "**Select workout routine**",
        pd.unique(st.session_state["data"][st.session_state["columns"]["WORKOUT_NAME"]]),
        on_change=on_workout_change
    )

    if st.session_state["updated_workout"]:
        sepump.update_workout_data(workout_filter)
        sepump.update_workout_data_agg()
        st.session_state["workout_data"] = sepump.workout_data
        st.session_state["workout_data_agg"] = sepump.workout_data_agg
    
    # 3a. Metrics
    v_space(1)
    st.write(f"##### :bar_chart: Metrics for workout routine *{workout_filter}*:")
    show_total_stats(st.session_state["workout_data"])

    # 3b. Graphs
    v_space(1)
    st.write(f"##### :chart_with_upwards_trend: Graphs for *{workout_filter}*:")
    metric_to_column_workout = {
        "Total Volume (per workout)": "total_volume",
        "Total Reps (per workout)": "total_reps"
    }
    graph_columns_workout = st.columns(2)
    for m, metric in enumerate(metric_to_column_workout.keys()):
        col_index = m % 2
        col = graph_columns_workout[col_index]
        chart = alt.Chart(
            st.session_state["workout_data_agg"], title=f"{metric} for {workout_filter}"
        ).mark_line(point=True).encode(
            x=alt.X("date", title="Date"),
            y=alt.Y(metric_to_column_workout[metric], title=metric),
        )
        chart += chart.transform_regression('date', metric_to_column_workout[metric]).mark_line(color="red")
        col.altair_chart(chart, use_container_width=True)

    ###########################################################################
    # 4. Combined Exercise and Workout filtering
    ###########################################################################

    st.divider()
    st.write("## 🔍 Filter by Exercise and Workout:")
    
    # Create two columns for the filters
    filter_col1, filter_col2 = st.columns(2)
    
    # Exercise filter
    selected_exercise = filter_col1.selectbox(
        "**Select exercise**",
        ["All"] + list(pd.unique(st.session_state["data"][st.session_state["columns"]["EXERCISE_NAME"]])),
        key="combined_exercise_filter"
    )
    
    # Workout filter
    selected_workout = filter_col2.selectbox(
        "**Select workout routine**",
        ["All"] + list(pd.unique(st.session_state["data"][st.session_state["columns"]["WORKOUT_NAME"]])),
        key="combined_workout_filter"
    )

    # Filter the data based on selections
    filtered_data = st.session_state["data"].copy()
    if selected_exercise != "All":
        filtered_data = filtered_data[filtered_data[st.session_state["columns"]["EXERCISE_NAME"]] == selected_exercise]
    if selected_workout != "All":
        filtered_data = filtered_data[filtered_data[st.session_state["columns"]["WORKOUT_NAME"]] == selected_workout]

    # Show metrics for filtered data
    if len(filtered_data) > 0:
        v_space(1)
        st.write("##### :bar_chart: Metrics for filtered data:")
        show_total_stats(filtered_data)

        # Add graphs for filtered data
        v_space(1)
        st.write("##### :chart_with_upwards_trend: Graphs for filtered data:")
        
        # Prepare aggregated data for graphs
        date_col = st.session_state["columns"]["DATE"]  # Get the correct date column name
        filtered_data_agg = filtered_data.groupby(date_col).agg({
            "volume": "sum",
            st.session_state["columns"]["REPS"]: "sum"
        }).reset_index()
        filtered_data_agg.columns = ["date", "total_volume", "total_reps"]

        metric_to_column_filtered = {
            "Total Volume (per workout)": "total_volume",
            "Total Reps (per workout)": "total_reps"
        }
        
        graph_columns_filtered = st.columns(2)
        for m, metric in enumerate(metric_to_column_filtered.keys()):
            col_index = m % 2
            col = graph_columns_filtered[col_index]
            chart = alt.Chart(
                filtered_data_agg, 
                title=f"{metric} for {selected_exercise if selected_exercise != 'All' else 'All Exercises'} "
                      f"in {selected_workout if selected_workout != 'All' else 'All Workouts'}"
            ).mark_line(point=True).encode(
                x=alt.X("date", title="Date"),
                y=alt.Y(metric_to_column_filtered[metric], title=metric),
            )
            chart += chart.transform_regression('date', metric_to_column_filtered[metric]).mark_line(color="red")
            col.altair_chart(chart, use_container_width=True)
    else:
        st.warning("No data available for the selected combination of exercise and workout.")
    
    # Reset update-triggers in session state to False.
    init_session_state_updates()
