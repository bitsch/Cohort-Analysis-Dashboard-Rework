from plotly.offline import plot 


def create_div_block(fig):
    """
    Creates a DIV block containing an plotly figure for displaying inside of an HTML
    """
    return plot(fig, output_type='div', show_link=False, link_text="")



def trace_plotting_styler(variant_tuple, offset = 3):
    
    sublists = [", ".join(variant_tuple[x:x+offset])  for x in range(0, len(variant_tuple), offset)]
    styled_variant = "<br>".join(sublists)
    
    return styled_variant