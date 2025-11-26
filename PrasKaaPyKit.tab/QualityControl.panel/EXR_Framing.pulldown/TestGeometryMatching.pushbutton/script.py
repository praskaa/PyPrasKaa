# -*- coding: utf-8 -*-
__title__ = 'Test Geometry Matching'
__doc__ = 'Test lib/geometry_matching.py'

import sys
import os
from Autodesk.Revit.DB import FilteredElementCollector, RevitLinkInstance
from pyrevit import revit, forms, script

# Add lib to path
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from geometry_matching import match_beams, FEET3_TO_MM3

doc = revit.doc
output = script.get_output()

def main():
    # Select link
    links = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not links:
        forms.alert("No links found")
        return
    
    link_dict = {link.Name: link for link in links}
    selected = forms.SelectFromList.show(sorted(link_dict.keys()), 
                                         title='Select Link', 
                                         button_name='OK')
    if not selected:
        return
    
    link_doc = link_dict[selected].GetLinkDocument()
    if not link_doc:
        forms.alert("Link not loaded")
        return
    
    # Get threshold
    thresh_str = forms.ask_for_string(
        prompt='Volume threshold (mm³):\n28316 = 0.001 cu ft (recommended)',
        default='28316'
    )
    
    vol_mm3 = float(thresh_str) if thresh_str else 28316
    vol_cuft = vol_mm3 / FEET3_TO_MM3
    
    # Run
    output.print_md("# Geometry Matching Test")
    output.print_md("Link: {}".format(selected))
    output.print_md("Threshold: {:,.0f} mm³".format(vol_mm3))
    output.print_md("---")
    
    res = match_beams(link_doc, vol_threshold=vol_cuft)
    
    # Results
    n_host = len(res['matches']) + len(res['unmatched'])
    time_per = res['time_s'] / n_host if n_host > 0 else 0
    
    output.print_md("**Total Time:** {:.2f}s ({:.4f}s/beam)".format(res['time_s'], time_per))
    if 'cache_time_s' in res['stats']:
        output.print_md("  - Cache: {:.2f}s | Match: {:.2f}s".format(
            res['stats']['cache_time_s'],
            res['stats']['match_time_s']
        ))
    output.print_md("**Beams:** {} host, {} linked ({} cached)".format(
        res['stats']['n_host'],
        res['stats']['n_linked'],
        res['stats']['n_cached']
    ))
    output.print_md("**Matched:** {} ({:.1f}%)".format(
        len(res['matches']), 
        float(res['match_rate']) * 100
    ))
    output.print_md("**Unmatched:** {}".format(len(res['unmatched'])))
    
    if time_per < 0.01:
        output.print_md("✅ Excellent!")
    elif time_per < 0.03:
        output.print_md("✅ Fast!")
    else:
        output.print_md("⚠️ Slow")
    
    # Summary
    msg = "Test Complete!\n\n"
    msg += "Time: {:.2f}s\n".format(res['time_s'])
    msg += "Matched: {} / {} ({:.1f}%)\n".format(
        len(res['matches']), 
        n_host, 
        float(res['match_rate']) * 100
    )
    forms.alert(msg)

if __name__ == '__main__':
    main()