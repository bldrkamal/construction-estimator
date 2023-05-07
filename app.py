import math
import pandas as pd
#from matplotlib.figure import Figure
from munch import Munch
from viktor import Color
from viktor import ViktorController, UserError
from viktor.parametrization import (
    ViktorParametrization, NumberField
    
)
from viktor.geometry import( Point, mirror_object,
                CircularExtrusion ,  Line,Group, LinearPattern, SquareBeam, Material)

from viktor.views import (
    DataView,
    GeometryAndDataResult,
    GeometryAndDataView,
    DataGroup,
    DataItem,
    DataResult
    
)


class Parametrization(ViktorParametrization):
     # Define the input fields
     length=NumberField('Length(L)', min=0, max=10,default=2, suffix="m")
     Width=NumberField('Width(W)', min=0, max=10,default=2, suffix="m")
     heigth=NumberField('Thickness', min=0, max=700, default=300,suffix="mm")
     spacing_main= NumberField('spacing of MB ', min=100, max=500,default=150, suffix="mm")
     spacing_distribution= NumberField('spacing of DB', min=100, max=500,default=150, suffix="mm")
     dia_main= NumberField('Dia. MB', min=8, max=32,default=12, suffix="mm")
     dia_distribution= NumberField('Dia. DB', min=8, max=32,default=12, suffix="mm")
     concrete_cover= NumberField('conc.cover', min=25, max=100,default=50, suffix="mm")
     Number_footing= NumberField('Nr. of footing',default=1, suffix="Nr")
     cement= NumberField('cement ',default=1, suffix="ratio")
     fine_agg= NumberField('Fine_agg',default=2, suffix="ratio")
     coarse_agg= NumberField('coarse_agg',default=4, suffix="ratio")


class Controller(ViktorController):
    label = "footing estimator"
    parametrization = Parametrization(width=37)


    @GeometryAndDataView("Footing geometry", duration_guess=1)
    def get_geometry_view(self, params, **kwargs):
        geometry_group = Group([])

        # Define Materials
        glass = Material("Glass", color=Color(150, 150, 255), threejs_opacity=0.4)
        rodmat = Material("reinforcement", color=Color.black())

        footing = SquareBeam(params.length, params.Width, (params.heigth/1000), material=glass)
        pa = Point(-params.length/2,-params.Width/2, 0)
        pb = Point(+params.length/2,-params.Width/2, 0)
        li = Line(pa,pb)
        qa = Point(-params.length/2,-params.Width/2, 0)
        qb = Point(-params.length/2,+params.Width/2, 0)
        qi = Line(qa,qb)
        rem=CircularExtrusion(params.dia_main/1000,li,material=rodmat)
        red=CircularExtrusion(params.dia_distribution/1000,qi,material=rodmat)
        # for starter bars
        st1=Line(Point(-0.2,0.2,0.01),Point(-0.2,0.2,2))
        st2=Line(Point(-0.2,-0.2,0.01),Point(-0.2,-0.2,2))
        st3=Line(Point(0.2,-0.2,0.01),Point(0.2,-0.2,2))
        st4=Line(Point(0.2,0.2,0.01),Point(0.2,0.2,2))
        st1=CircularExtrusion(0.030,st1,material=rodmat)
        st2=CircularExtrusion(0.03,st2,material=rodmat)
        st3=CircularExtrusion(0.03,st3,material=rodmat)
        st4=CircularExtrusion(0.03,st4,material=rodmat)
        
        s=params.spacing_main/1000
        #dm=params.dm/1000
        c=(params.concrete_cover/1000)
        h=(params.heigth/1000)
        dm=params.dia_main/1000
        dd=params.dia_distribution/1000
        sd=params.spacing_distribution/1000
        #li.translate(0,0,0)
        
        footing.translate((0,0,0))
        #rem.translate((0,0,0))
        #qi.translate((0,0,0))
        #reb = mirror_object(rem, Point(0, 0, 0), (1, 1, 0))
        
        
        # Pattern (duplicate) the floor to create a building
        Mb=((params.Width-(2*c))/s)+1
        Db=((params.length-(2*c))/sd)+1
        Mb=round(Mb)
        Db=round(Db)
        vab= LinearPattern(rem, direction=[0, 1, 0], number_of_elements=Mb, spacing=params.spacing_main/1000)
        yab= LinearPattern(red, direction=[1, 0, 0], number_of_elements=Db, spacing=params.spacing_distribution/1000)

        #number of reinforcement at the length and width of the footing
        
        Mb1=(Mb*params.Number_footing)
        Db2=(Db*params.Number_footing)

        # Cutting Length of Main Reinforcement 
        Cm1 = round((params.length-(2*c))+(2*h)-(4*c)-(2*2*dm),2)
        # Cutting Length of distribution Reinforcement
        Cm2 = round(((params.Width-(2*c))+(2*h)-(4*c)-(2*2*dd)),2)
        #total Cutting Length of Main Reinforcement
        
        TCm1=Cm1*Mb1
        # total Cutting Length of distribution Reinforcement
        TCm2=Cm2*Db2
        txt1="Nr Y{}".format(params.dia_main)
        txt2="Nr Y{}".format(params.dia_distribution)
       
        geometry_group.add([footing,vab,yab,st1,st2,st3,st4])
        data = DataGroup(
            DataItem('Number of footing', params.Number_footing,suffix="Nr"),
            DataItem('Main bars(MB)', Mb1,suffix="Nr"),
            DataItem('Distri.bars(DB)',Db2,suffix="Nr"),
            DataItem('Cuting L. (MB)', Cm1, suffix="m"),
            DataItem('Cutting L. (DB)', Cm2, suffix="m"),
            DataItem('Total L. (MB)', round(TCm1,2), suffix="m"),
            DataItem('Total L. (DB)', round(TCm2,2), suffix="m"),
            DataItem('NR reinf(MB)12m:', round(TCm1/12),suffix=txt1),
            DataItem('NR reinf(DB)12m:', round(TCm2/12),suffix=txt2)
            
            )
        return GeometryAndDataResult(geometry_group,data)
    
    
    @DataView("Concrete material", duration_guess=1)
    def show_volume(self, params, **kwargs):
        volume = (params.length * params.Width * (params.heigth/1000))
        volume_total=volume*params.Number_footing
        #cement mass
        density_cement=1440 #kg/m3

        total_mix_volume=params.cement+params.fine_agg+params.coarse_agg
        mass_cement=(params.cement/total_mix_volume)*density_cement*1.54
        #number of cement
        cementBags=mass_cement/50

        #density of fine aggregate
        ratio_fineAgg_volume=params.fine_agg/total_mix_volume
        mass_fineAgg=ratio_fineAgg_volume*1650*1.54*1.2

        #density of coarse concrete
        ratio_coarseAgg_volume=params.coarse_agg/total_mix_volume
        mass_coarseagg=ratio_coarseAgg_volume*1650*1.54*1.15
    

        data = DataGroup(
            DataItem('Volume of concrete', round(volume_total,2), suffix='m3'),
            DataItem('cement bags', math.ceil(cementBags*params.Number_footing*volume_total), suffix='Nr'),
            DataItem('mass_fine_agg', round(mass_fineAgg*params.Number_footing*volume_total) , suffix='kg'),
            DataItem('mass_coarse_agg', round(mass_coarseagg*params.Number_footing*volume_total ), suffix='kg')
            #DataItem('main bar', self.Nb)

            
        )

        return DataResult(data)
    

    
    