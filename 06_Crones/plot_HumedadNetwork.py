#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cprv1.cprv1 as cpr

import datetime
import pandas as pd
import numpy as np
import multiprocessing
import time
#paquetes sora
import alarmas as al
import glob
import json
import datetime as dt
import cprsora.humedad as hm
from cpr import cpr as cpr_1

def logger(orig_func):
    '''logging decorator, alters function passed as argument and creates
    log file. (contains function time execution)
    Parameters
    ----------
    orig_func : function to pass into decorator
    Returns
    -------
    log file
    '''
    import logging
    from functools import wraps
    import time
    logging.basicConfig(filename = 'plot_HumedadNetwork.log',level=logging.INFO)
    @wraps(orig_func)
    def wrapper(*args,**kwargs):
        start = time.time()
        f = orig_func(*args,**kwargs)
        date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        took = time.time()-start
        log = '%s:%s:%.1f sec'%(date,orig_func.__name__,took)
        print log
        logging.info(log)
        return f
    return wrapper

@logger
def plot_HNetwork(nivel):
#     nivel=cprv1.Nivel(user='sora',passwd='12345',codigo=99)
    queryH=nivel.read_sql('select codigo from estaciones_estaciones where clase="H"')
    codes=np.array(queryH['codigo'])
    rutacredentials_remote='/media/nicolas/Home/Jupyter/Soraya/git/nontrackablefiles/remotecredentials.json'
    rutacredentials_local='/media/nicolas/Home/Jupyter/Soraya/git/nontrackablefiles/localcredentials.json'

    with open(rutacredentials_local) as json_file:  
        localcredentials = json.load(json_file)
    ruta_figs='/media/nicolas/Home/Jupyter/Soraya/Op_Alarmas/Result_to_web/figs_operacionales/'
    for code in codes:
        self= hm.Humedad(codigo=code, **localcredentials)
        end = dt.datetime.now()
        starts  = [(end - dt.timedelta(hours=3)), (end - dt.timedelta(hours=24)),
                   (end - dt.timedelta(hours=72)),(end - dt.timedelta(days=30)) ]
        for start in starts:
            #consulta pluvio
            pluvio = cpr_1.Pluvio(int(self.info.get('pluvios')))
            pluvio_s = pluvio.read_pluvio(start,end)
            self.plot_Humedad2Webpage(start,end,pluvio_s,ruta_figs,rutacredentials_remote,rutacredentials_local)
    print 'Se ejecutan las graficas operacionales de la red de humedad'

#EJECUCION

self = cpr.Nivel(codigo = 99,user='sample_user',passwd='s@mple_p@ss',SimuBasin=False)

# Plots de Red de Humedad,ejecuta plots en paralelo   
if __name__ == '__main__':
    p = multiprocessing.Process(target=plot_HNetwork,args=(self,), name="r")
    p.start()
    time.sleep(250) # wait near 5 minutes to kill process
    p.terminate()
    p.join()
    print 'plot_HNetwork executed'
