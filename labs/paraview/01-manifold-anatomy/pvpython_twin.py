"""ParaView (pvpython) twin of render_lab.py: same pipeline, same views.
Run inside ParaView or with pvbatch where a ParaView install exists."""
from paraview.simple import (OpenDataFile, StreamTracer, Slice, Show,
                             ColorBy, GetActiveViewOrCreate, SaveScreenshot)
src = OpenDataFile("internal.vtu")
st = StreamTracer(Input=src, SeedType="Point Cloud")
st.Vectors = ["POINTS", "U"]
st.SeedType.NumberOfPoints = 48
view = GetActiveViewOrCreate("RenderView")
view.Background = [14/255, 22/255, 38/255]
d = Show(st, view); ColorBy(d, ("POINTS", "U", "Magnitude"))
SaveScreenshot("pv1_streamlines_paraview.png", view, ImageResolution=[1500, 950])
sl = Slice(Input=src); sl.SliceType.Normal = [0, 1, 0]
d2 = Show(sl, view); ColorBy(d2, ("POINTS", "U", "Magnitude"))
SaveScreenshot("pv1_slice_paraview.png", view, ImageResolution=[1500, 700])
