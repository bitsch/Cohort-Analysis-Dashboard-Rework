import group_analysis.plotting.data_frame_creation as plotting_data
import group_analysis.plotting.plot_creation as plotting
from   group_analysis.group_managment.group import Group

def demo_hospital(log, log_format, log_information):
    """
    Simple Demo, for the Hospital.xes, to test the plotting and data conversion.
    """
    Groups = [
             Group(name = "Inform Authority", members = ['Inform Authority Fill Form','Inform Authority Send Form']),
             Group(name = "Check Treat", members = ['Check Treatment A1','Check Treatment A2', 'Check Treatment A3'])
             ]

    df = plotting_data.create_plotting_data(log, "csv", log_information)
    date_frame = plotting_data.create_concurrency_frame(df, Groups)

    concurrency_plt_div = plotting.concurrency_plot_factory(date_frame, Groups, freq = "D", aggregate = max)    
    timeframe_plt_div =  plotting.amplitude_plot_factory(date_frame, Groups)

    context = {'concurrency_plt_div': concurrency_plt_div,
               'timeframe_plt_div' : timeframe_plt_div,
               }

    return context

