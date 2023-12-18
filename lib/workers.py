import os
import pandas as pd
import sys
from pathlib import Path


ROOT_dir = Path(__file__).parent.parent
sys.path.append(ROOT_dir)
sys.path.insert(0, os.path.join(ROOT_dir, '/lib'))


def personplan2df(person, plan, output=True, experienced=False):
    """
    Convert a person's activity plan from MATSim format to a dataframe.
    :param person: matsim.plan_reader() object
    :param plan: matsim.plan_reader() object
    :param output: whether read in output file
    :param experienced: whether read in experienced plans
    :return: a re-organised individual activity plan executed by matsim (dataframe)
    """
    pid = person.attrib['id']

    activities = filter(lambda x: x.tag == 'activity', plan)
    types = [activity.attrib['type'] for activity in activities]
    activities = filter(lambda x: x.tag == 'activity', plan)
    end_times = []
    for activity in activities:
        try:
            end_times.append(activity.attrib['end_time'])
        except:
            end_times.append('23:59:59')
    if experienced:
        activities = filter(lambda x: x.tag == 'activity', plan)
        xs = [0]
        count = 0
        for activity in activities:
            if count != 0:
                xs.append(activity.attrib['x'])
            count += 1
        activities = filter(lambda x: x.tag == 'activity', plan)
        ys = [0]
        count = 0
        for activity in activities:
            if count != 0:
                ys.append(activity.attrib['y'])
            count += 1
    else:
        activities = filter(lambda x: x.tag == 'activity', plan)
        xs = [activity.attrib['x'] for activity in activities]
        activities = filter(lambda x: x.tag == 'activity', plan)
        ys = [activity.attrib['y'] for activity in activities]

    legs = filter(lambda x: x.tag == 'leg', plan)
    modes = [leg.attrib['mode'] for leg in legs]
    modes = [''] + modes

    df = pd.DataFrame()
    df.loc[:, 'act_purpose'] = types
    df.loc[:, 'PId'] = pid
    df.loc[:, 'act_end'] = end_times
    df.loc[:, 'act_id'] = range(0, len(types))
    df.loc[:, 'mode'] = modes
    df.loc[:, 'POINT_X'] = xs
    df.loc[:, 'POINT_Y'] = ys

    if output:
        legs = filter(lambda x: x.tag == 'leg', plan)
        trav_times = [leg.attrib['trav_time'] for leg in legs]
        trav_times = ["00:00:00"] + trav_times

        legs = filter(lambda x: x.tag == 'leg', plan)
        dep_times = [leg.attrib['dep_time'] for leg in legs]
        dep_times = ["00:00:00"] + dep_times

        legs = filter(lambda x: x.tag == 'leg', plan)
        distances = [0]
        for leg in legs:
            routes = filter(lambda x: x.tag == 'route', leg)
            distances += [float(route.attrib['distance']) / 1000 for route in routes]

        df.loc[:, 'dep_time'] = dep_times
        df.loc[:, 'trav_time'] = trav_times
        df.loc[:, 'distance'] = distances
        df.loc[:, 'score'] = float(plan.attrib['score'])
    else:
        df.loc[:, 'dep_time'] = ["00:00:00"] + list(df.loc[:, 'act_end'].values[:-1])
        # df.loc[:, 'trav_time'] = 0  # Only for output
        # df.loc[:, 'distance'] = 0  # Only for output
        # df.loc[:, 'speed'] = 0  # Only for output
        df.loc[:, 'src'] = 'input'
        df.loc[:, 'score'] = 0
    return df


def plans_summary(df):
    """
    :param df: dataframe, containing multiple agents' plans
    :return: dataframe, containing multiple agents' plans with more information
    """
    # calculate travel time
    df.loc[:, 'trav_time_min'] = df.trav_time.apply(lambda x: pd.Timedelta("0 days " + x))
    df.loc[:, 'trav_time_min'] = df.loc[:, 'trav_time_min'].apply(lambda x: x.seconds / 60)
    df.loc[:, 'speed'] = df.loc[:, 'distance'] / (df.loc[:, 'trav_time_min'] / 60)  # km/h

    # act_end - dep_time + trav_time = act_time for 1:
    df.loc[:, 'act_end_t'] = df.act_end.apply(
        lambda x: pd.Timedelta("0 days " + x) if x.split(':')[0] != '24' else pd.Timedelta(
            "1 days " + ':'.join(['00'] + x.split(':')[1:])))
    df.loc[:, 'dep_time_t'] = df.dep_time.apply(
        lambda x: pd.Timedelta("0 days " + x) if x.split(':')[0] != '24' else pd.Timedelta(
            "1 days " + ':'.join(['00'] + x.split(':')[1:])))
    df.loc[:, 'trav_time_t'] = df.trav_time.apply(lambda x: pd.Timedelta("0 days " + x))
    df.loc[:, 'act_time'] = df.apply(
        lambda row: (row['act_end_t'].seconds - row['dep_time_t'].seconds - row['trav_time_t'].seconds) / 60 if row[
                                                                                                                    'act_id'] != 0 else
        row['act_end_t'].seconds / 60, axis=1)
    # df.loc[:, 'act_time'] = df.loc[:, 'act_time'].apply(lambda x: x if x <= 1440 else x - 1440)
    df.drop(columns=['act_end_t', 'dep_time_t', 'trav_time_t'], inplace=True)

    # Convert act_end into the input format
    df.loc[:, 'act_end'] = df.act_end.apply(
        lambda x: pd.Timedelta("0 days " + x) if x.split(':')[0] != '24' else pd.Timedelta(
            "1 days " + ':'.join(['00'] + x.split(':')[1:])))
    df.loc[:, 'act_end'] = df.act_end.apply(lambda x: x.seconds / 3600)

    # Convert act_end into the input format
    df.loc[:, 'dep_time'] = df.dep_time.apply(
        lambda x: pd.Timedelta("0 days " + x) if x.split(':')[0] != '24' else pd.Timedelta(
            "1 days " + ':'.join(['00'] + x.split(':')[1:])))
    df.loc[:, 'dep_time'] = df.dep_time.apply(lambda x: x.seconds / 3600)  # hour
    df.loc[:, 'src'] = 'output'
    return df

