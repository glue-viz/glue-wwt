from glue.core import Data, DataCollection
from glue.utils.qt import get_qapp
from glue.core.session import Session
import numpy as np
from glue_wwt.viewer.data_viewer import WWTDataViewer

app = get_qapp()

d = Data(label="data",
         RAJ2000=np.random.uniform(0, 90, 100),
         DEJ2000=np.random.uniform(-30, 30, 100))
dc = DataCollection([d])
session = Session(data_collection=dc)

wwt = WWTDataViewer(session)
wwt.add_data(d)
wwt.show()
wwt.options_widget().show()
for widget in wwt._view.layout_style_widgets.values():
    print(widget)
    widget.show()
    widget.raise_()
app.exec_()
