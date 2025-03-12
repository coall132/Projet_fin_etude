from django.shortcuts import render, redirect
from utils import get_db_mongo
from django.contrib.auth.decorators import login_required
import pandas as pd
from pymongo import MongoClient
from django.contrib.auth import get_user_model
from .models import Project, Dataset
from django.conf import settings
from .forms import UploadFileForm
import gridfs
from pyspark.sql import SparkSession
import os
import uuid 
from io import BytesIO

mongo_config = settings.MONGO_CONFIG

# Utilisation de get_user_model pour obtenir le modèle utilisateur correct
User = get_user_model()

# Create your views here.
def home(request):
    return render(request, 'accueil.html')

@login_required
def espace_personel(request):
    username=request.user.username
    return render(request, 'espace_perso.html',{'username': username})

@login_required
def liste_project(request):
    user = request.user
    dico_project = dict(Project.objects.filter(user=user).values_list('project_name', 'project_id')) 
    if request.method == 'POST':
        action, projet = request.POST.get('action_liste_prj', None), request.POST.get('projet', None)
        if action == 'action1':
            Project.objects.get(user=user, project_id=projet).delete()
            dico_project = dict(Project.objects.filter(user=user).values_list('project_name', 'project_id'))
    return render(request, 'liste_project.html', {'projects': dico_project,})

@login_required
def creer_project(request):
    user = request.user
    if request.method == 'POST':
        project_name = request.POST.get("nom_projet")
        if project_name: 
            try :
                Project.objects.create(user=user,project_name=project_name)
            except :
                pass
    return redirect('liste_project')

@login_required
def project(request,project_id):
    user = request.user
    test= Project.objects.get(user=user, project_id=project_id)
    storage = Storage_df()
    if Project.objects.filter(user=user, project_id=project_id).exists() :
        try :
            dict_dataset = dict(Dataset.objects.filter(project_id=project_id).values_list('dataset_name', 'dataset_id'))
        except Exception as e:
            dict_dataset=None
    if request.method == 'POST':
        filename = request.POST.get('filename', None)
        action = request.POST.get('action', None)
        if action=="action" and filename : 
            df = find_df(user.username,int(filename),test.project_name)
            id_df = storage.save(df)
            print(id_df)
    return render(request,'project.html',{'project_id':project_id,"dict_dataset":dict_dataset})

@login_required
def upload_csv(request,project_id):
    task_id = request.session.get("task_id", None)
    user=request.user
    db,client = get_db_mongo(mongo_config["DB_NAME"],mongo_config["HOST"],27017,mongo_config["USER"],mongo_config["PASSWORD"])
    fs = gridfs.GridFS(db)
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']   
            projet_name=Project.objects.get(user=user, project_id=project_id).project_name  
            project = Project.objects.get(user=user, project_id=project_id) 
            if projet_name:
                if not Dataset.objects.filter(project_id=project_id, dataset_name=csv_file.name).exists():
                    dataset=Dataset.objects.create(project_id=project,dataset_name=csv_file.name,description=None)
                    file_id = fs.put(
                        csv_file, 
                        filename={'csv_file_name':csv_file.name,'username':user.username,'id_file':dataset.dataset_id}, 
                        metadata={"username": user.username,'filename':csv_file.name,'project_name':projet_name,'id_file':dataset.dataset_id},
                        chunkSizeBytes=1048576 )
        client.close()       
    else :
        client.close()
        form = UploadFileForm()
    return redirect('project',project_id)

def find_df(username,file_id,project_name):
    db, client = get_db_mongo(mongo_config["DB_NAME"],mongo_config["HOST"],27017,mongo_config["USER"],mongo_config["PASSWORD"])
    fs = gridfs.GridFS(db)
    grid_out = fs.find_one({"metadata.username": username, 'metadata.id_file': file_id,'metadata.project_name':project_name})
    if grid_out:
        file_data = BytesIO(grid_out.read())
        df = pd.read_csv(file_data,sep=',',on_bad_lines='warn')
        return df

class Storage_df:
    def __init__(self,storage_dir="spark_dataframes"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)  # Crée le dossier s'il n'existe pas
        self.spark = SparkSession.builder.appName("SparkDataFrameStorage").master("local[*]").config("spark.driver.memory", "8g").config("spark.executor.memory", "16g").config("spark.sql.shuffle.partitions", "400").getOrCreate()
    def save(self,df):
        if isinstance(df, pd.DataFrame):  # Vérifie si c'est un DataFrame Pandas
            df = self.spark.createDataFrame(df)
        df_id = str(uuid.uuid4())  # Génère un ID unique
        file_path = os.path.join(self.storage_dir, df_id)
        df.write.parquet(file_path, mode="overwrite")  # Écrit en format Parquet
        print(f"✅ DataFrame enregistré sous l'ID: {df_id}")
        return df_id
    def load(self, df_id):
        """Charge un DataFrame Spark à partir de son ID."""
        file_path = os.path.join(self.storage_dir, df_id)
        if os.path.exists(file_path):
            df = self.spark.read.parquet(file_path)
            print(f"✅ DataFrame chargé avec succès (ID: {df_id})")
            return df
        else:
            print(f"❌ Aucune donnée trouvée pour l'ID: {df_id}")
            return None
    def list_files(self):
        """Liste tous les fichiers enregistrés."""
        return [f for f in os.listdir(self.storage_dir) if os.path.isdir(os.path.join(self.storage_dir, f))]



class Df_perso:
    def __init__(self,df):
        self.user=df.copy()
    def info_df(self):
        self.ligne = self.df.shape[0]
        self.colonne = self.df.shape[1]
        self.nb_nul = self.df.isnull().sum().to_frame().to_html()
        self.nb_colonne_double = self.df.duplicated().sum()
        return self.ligne,self.colonne,self.nb_nul,self.nb_colonne_double
    def magic_clean(self):
        for col in self.df.select_dtypes(include=['object']).columns:
            self.df[col] = self.df[col].astype(str).str.replace(r'[\s\x00-\x1F\x7F-\x9F]+', '', regex=True)
            self.df[col] = pd.to_numeric(self.df[col], errors='ignore')
            self.df[col] = self.df[col].astype(str).str.replace(',', '.', regex=False)
            try :
                converted = pd.to_numeric(self.df[col], errors='raise')
                if converted.notna().all():
                    try:
                        self.df[col]=self.df[col].astype(int)
                    except:
                        self.df[col]=self.df[col].astype(float)
            except :
                test1=self.df[col].apply(lambda x: isinstance(x, dict)).all()
                test2=self.df[col].apply(lambda x: isinstance(x, list)).all()
                if test1==True or test2==True:
                    pass
                else:
                    self.df[col]=self.df[col].astype(str)
        return self.df
    def type_column(self):
        df_cleaned=self.magic_clean()
        self.categorical_column=df_cleaned.select_dtypes(include=["category",'object']).columns.tolist()
        self.numerical_column=df_cleaned.select_dtypes(include=['number']).columns.tolist()
        return self.categorical_column, self.numerical_column
    def colonne_type(self):
        return {
            col: type(self.df[col].dropna().iloc[0]).__name__ if not self.df[col].dropna().empty else 'NoneType'
            for col in self.df.columns
        }
    def afficher_df(self):
        self.columns=self.df.columns   
        self.dico_type=self.colonne_type()
        self.rows = self.df.reset_index().to_dict(orient='records')
        return self.columns,self.dico_type,self.rows

class Bdd_user:
    def __init__(self,db_name_m,host_m,port_m,username_m,password_m):
        self.db_name_m=db_name_m
        self.host_m=host_m
        self.port_m=port_m
        self.username_m=username_m
        self.password_m=password_m
    def get_db_mongo(self):
        self.client = MongoClient(host=self.host_m,
                            port=int(self.port_m),
                            username=self.username_m,
                            password=self.password_m
                            )
        self.db_mongo = self.client[self.db_name_m]
        return self.db_mongo, self.client

    