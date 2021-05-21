 


import group_analysis.datetime_utils as dt_utils
import group_analysis.group_managment as gm
import group_analysis.log_import_util as log_import
import group_analysis.plotting as plotting
import group_analysis.utils as utils
from group_analysis.group_managment import Group

def demo_hospital(log, log_format, log_information):
    """
    Simple Demo, for the Hospital.xes, to test the plotting and data conversion.
    """
    Groups = [Group(name = "Release", members = ['Release B','Release A','Release D','Release C', 'Release E']),
                      Group(name = "Emergency Room", members = ['ER Triage', 'ER Registration', 'ER Sepsis Triage']),
                      Group(name = "Admission", members = ['Admission NC', 'Admission IC']),
                      Group(name = "IV", members = ['IV Antibiotics', 'IV Liquid']), 
                      Group(name = "Treat", members = ['LacticAcid', 'Leucocytes'])
                      ]


    date_frame = log_import.create_plotting_data(log, Groups, log_format, log_information, floor_freq = "H")

    concurrency_plt_div = plotting.concurrency_plot_factory(date_frame, Groups, freq = "W", aggregate = max)
    timeframe_plt_div = plotting.amplitude_plot_factory(date_frame, Groups)           
    bar_timeframe_plt_div =  plotting.timeframe_plot_factory(date_frame, Groups)
    df_lifetime = log_import.create_group_lifetime_dataframe_from_dateframe(date_frame, Groups)
    lifetime_plt_div = plotting.lifetime_plot_factory(df_lifetime)

    context = {'concurrency_plt_div': concurrency_plt_div,
               'timeframe_plt_div': timeframe_plt_div,
               'bar_timeframe_plt_div' : bar_timeframe_plt_div,
               'lifetime_plt_div' : lifetime_plt_div}
    return context
