import pywhatkit as kit
from datetime import datetime

data_atual = datetime.now()

# kit.sendwhatmsg_instantly("+5521999999999",
                        #   "Bora automatizar o zapzap com Python, beleza?")

kit.sendwhatmsg("+5521999999999",
                "Bora automatizar o zapzap com Python, beleza?",
                data_atual.hour,
                data_atual.minute + 2)