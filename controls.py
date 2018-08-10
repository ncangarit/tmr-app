# flake8: noqa

# In[]:
# Controls for webapp
#Comunidad	Poblacion	Publicación bicicleta	Conexión bicicleta	Publicación carro	Publicación carro,
# sin conexión	Conexión carro	Publicación caminante 	Conexión caminante	Pasajero	Hora almuerzo	Fines de semana
# Create a dictionary in case the value to display in the table is different from the one on the loaded DF
PARAMS_COLS = {
    'Comunidad':'Comunidad',
    'Población': 'Población',
    'Población con parqueadero': 'Población con parqueadero',
    'Publicación bicicleta': 'Publicación bicicleta',
    'Conexión bicicleta': 'Conexión bicicleta',
    'Publicación carro': 'Publicación carro',
    'Publicación carro, sin conexión': 'Publicación carro, sin conexión',
    'Conexión carro': 'Conexión carro',
    'Publicación caminante': 'Publicación caminante',
    'Conexión caminante': 'Conexión caminante',
    'Pasajero': 'Pasajero',
    'Excluir hora almuerzo': 'Hora almuerzo',
    'Excluir fines de semana':'Fines de semana',
    'Latitud':'Latitud',
    'Longitud': 'Longitud'
}

DEFAULT_params = {
    'Comunidad': '',
    'Población': 1000,
    'Población con parqueadero':800,
    'Publicación bicicleta': 1,
    'Conexión bicicleta': 1,
    'Publicación carro': 1,
    'Publicación carro, sin conexión': 0,
    'Conexión carro': 1,
    'Publicación caminante': 1,
    'Conexión caminante': 1,
    'Pasajero': 1,
    'Excluir hora almuerzo': 'SI',
    'Excluir fines de semana':'NO',
    'DEFAULT_PARAMS':'YES'

}


COMMUTE_MODE = {'walking': 'caminata',
                'taxi': 'taxi',
                'own_car': 'carro',
                'motorcycle':'moto',
                'bus': 'bus',
                'bicycle': 'bici'

                }

RIDE_TYPE = {'walk': 'caminata',
             'car': 'carro',
              'bicycle': 'bici'
                }

KPIS_HEADERS =[
    '% Usuarios registrados',
    '% Usuarios activos',
    '% Usuarios con parqueadero que publican',
    'Efectividad de uso (conexiones / publicaciones)'
]


TRANSPORT_TYPE1 = {
    'all': 'all',
    'bicycle': 'bicycle',
    'car': 'car',
    'van': 'van',
    'walk': 'walk'
}
TRANSPORT_TYPE = {
    'TODOS': 'all',
    'CARRO': 'car',
    'BICICLETA': 'bicycle',
    'CAMINATA': 'walk',
    'VAN': 'van'
}


COLORS_TABLE = [
    {
        'background': '#10ac84',#146b3a', #green
        'text': 'rgb(30, 30, 30)'
    },
    {
        'background': '#feca57', #f8b229', #yellow
        'text': 'rgb(30, 30, 30)'
    },
    {
        'background': '#ee5253', #bb2528', #red
        'text': 'white'
    },

]

SEMAFORO_METAS = {
    'VERDE': 70,
    'ROJO': 50
}

