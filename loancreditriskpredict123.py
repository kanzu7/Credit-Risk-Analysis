# -*- coding: utf-8 -*-
"""LoanCreditRiskPredict.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Z79YFserqbuZbJZBDo4RWwic6KIP6pju

### Import Library
"""

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

!pip install scorecardpy
import scorecardpy as sc

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV, GridSearchCV
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.metrics import plot_roc_curve
from sklearn.metrics import roc_auc_score, roc_curve, RocCurveDisplay, precision_recall_curve, PrecisionRecallDisplay
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, classification_report
from sklearn.metrics import accuracy_score
from sklearn import metrics
from sklearn.feature_selection import VarianceThreshold
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_validate
!pip install feature_engine
from feature_engine.selection import DropCorrelatedFeatures, SmartCorrelatedSelection

import warnings
warnings.filterwarnings("ignore")

sns.set(style='whitegrid')
sns.set_palette("bright")

# %matplotlib inline
# %config InlineBackend.figure_format = 'retina'

"""### Load Data Set"""

df = pd.read_csv("loan_data_2007_2014.csv")
df.head()

"""### Data Cleaning"""

# Cek setiap kolom data untuk mengetahui kolom yg memiliki missing value dan data uniq
dfdesc = []
for i in df.columns :
    dfdesc.append([i, len(df[i]),
                    df[i].dtypes,
                    df[i].isna().sum(),
                    round(((df[i].isna().sum()/(len(df)))*100),2),
                    df[i].nunique(),
                    df[i].drop_duplicates().sample(2, replace=True).values])
pd.DataFrame(dfdesc, columns=['dataFeatures','dataLength','dataType','null','nullPct','unique','uniqueSample'])

"""1. terdapat beberapa kolom yang tidak memiliki nilai sama sekali, hal ini mungkin terjadi karena beberapa hal, seperti :
    a. kesalahan join kolom,
    b. tidak terdapat record historis pada kolom kolom tersebut

2. Pada kolom tot_coll_amt, dan tot_cut_bal, missing value akan di isi dengan imputasi nol, kemungkinan missing values masuk akal jika di impute dengan nilai 0 karena tidak ada catatan historis, sedangkan untuk total_rev_hi_lim adalah kolom batas kredit jadi akan diimputasi dengan nilai mediannya
"""

df['tot_coll_amt'] = df['tot_coll_amt'].fillna(0)
df["tot_cur_bal"] = df["tot_cur_bal"].fillna(0)
df["total_rev_hi_lim"]  = df['total_rev_hi_lim'].fillna(df['total_rev_hi_lim'].median())

#check missing values again
df.isnull().sum()/len(df) * 100

#hapus kolom yang tidak memiliki values dan missing values lebih dari 30%
list_drop = [x for x in df.columns if df[x].isnull().sum()/len(df) * 100 > 30]
list_drop

df = df.drop(list_drop,axis=1)
df.shape

#Handling missing value
mv = df.isnull().sum().sort_values(ascending = False)
non_mv = df.notnull().sum()
percent = (df.isnull().sum()/df.isnull().count()*100).sort_values(ascending = False)
dtypes = df.dtypes
mv_df = pd.concat([mv, non_mv, percent, dtypes], axis=1, keys=['Missing', 'Non-Missing', 'Percent', 'Dtypes'])
mv_df

df[df["acc_now_delinq"].isna()]

df[(df["annual_inc"].isna())].shape

#karena annual_inc hanya ada 4 rows, jadi kita hapus saja
df = df.dropna(subset=['annual_inc']).reset_index(drop=True)
df.shape

df[df['delinq_2yrs'].isna()]

"""jika dilihat bahwa missing values pada kolom **delinq_2yrs**, terlihat kolom **delin1_2yrs** mising values karena tidak ada catatan historis. kolom **delinq_2yrs** memiliki keterkaitan dengan kolom seperti **collections_12_mths_ex_med**, **acc_now_delinq**, **revol_util**, **total_acc**,**open_acc** maka kolom kolom ini akan di imputasi 0 juga"""

df['delinq_2yrs'] = df['delinq_2yrs'].fillna(0)
df['inq_last_6mths'] = df['inq_last_6mths'].fillna(0)
df["total_acc"] = df["total_acc"].fillna(1)
df['revol_util'] = df['revol_util'].fillna(df['revol_util'].median())
df["pub_rec"] = df["pub_rec"].fillna(0)
df["collections_12_mths_ex_med"] = df["collections_12_mths_ex_med"].fillna(0)
df['acc_now_delinq'] = df['acc_now_delinq'].fillna(0)
df["open_acc"] = df["open_acc"].fillna(0)

"""Membuat kolom baru bernama **emp_length_int** untuk menyimpan nilai dari **emp_length** yang dijadikan **int**
**emp_length** < 1 years dijadikan nilai 0 years, missing values pada kolom ini akan dianggap **not have experience job**
"""

#processing kolom yang memiliki missing values
df['emp_length_int'] = df['emp_length'].str.replace('\+ years', '')
df['emp_length_int'] = df['emp_length_int'].str.replace('< 1 year', str(0))
df['emp_length_int'] = df['emp_length_int'].str.replace('n/a',  str(0))
df['emp_length_int'] = df['emp_length_int'].str.replace(' years', '')
df['emp_length_int'] = df['emp_length_int'].str.replace(' year', '')

df['emp_length_int'] = pd.to_numeric(df['emp_length_int'])
# Transforms the values to numeric.

#impute 0 
df["emp_length_int"] =df["emp_length_int"].fillna(0)

"""- beberapa kolom tidak relevan dalam faktor yang menentukan ciri khas yang menentukan seorang nasabah dapat membayar pinjaman atau tidak sehingga beberapa kolom yang di rasa tidak relevan akan dihapus
- machine learning yang akan dirancang, tidak menyertakan demographics wilayah agar machine learning tidak melakukan diskriminasi pada suatu daerah/wilayah sehingga kolom yang berhubungan dengan demographics akan dihapus
"""

#hapus beberapa kolom
df = df.drop(['Unnamed: 0',
              "id",
             "member_id",
             'title',
              'zip_code',
              'addr_state',
             "earliest_cr_line",
             "url",
             "issue_d",
             "emp_title",
             "policy_code",
             "emp_length",
             "last_credit_pull_d",
             "last_pymnt_d",
             "application_type"],axis=1)
df = df.reset_index(drop=True)

100*(df.isnull().sum())/len(df)

"""### Feature Selection Based on Information Value

### Target Definition
Nasabah yang status pinjamannya adalah 'Charged Off','Default','Late (16-30 days)','Late (31-120 days)','Does not meet the credit policy. Status:Charged Off',"Does not meet the credit policy. Status:Fully Paid". kita definisikan sebagai nasabah dengan kategori **bad** dan diberi flag 0, selain itu nasabah dengan kategori **good** akan diberi flag 1. untuk 'current' dan 'in grace period' tidak dapat digunakan karena belum dapat dipastikan apakah merupakan peminjam yang menunggak atau tidak
"""

df["loan_status"].unique()

#filtering data, exclude 'load_status Current' and 'in grace period'
df = df[~(df["loan_status"].isin(["Current","In Grace Period"]))]

#replacing home_ownership
df["home_ownership"] = df['home_ownership'].replace(["NONE","ANY"],["OTHER","OTHER"])

df["good_bad"] = np.where(df['loan_status'].isin(['Charged Off','Default','Late (16-30 days)',
       'Late (31-120 days)','Does not meet the credit policy. Status:Charged Off',"Does not meet the credit policy. Status:Fully Paid"]),0,1)

#drop kolom loan_status
df = df.drop("loan_status",axis=1)

#check
df["good_bad"].value_counts()

plt.figure(figsize=(8,6),dpi=100)
plt.title("Proportion Good and Bad Borrower",fontsize=12)
plt.pie(df["good_bad"].value_counts(),labels=["Good","Bad"],
       autopct='%1.1f%%',colors=["b","y"]);

"""**WOE** atau Weight of Evidence kita gunakan untuk mengukur antara nasabah baik dan buruk
nilai dari **WOE** ini akan digunakan untuk menghitung **IV** atau Infromation Value
"""

import pandas as pd
import scipy.stats as stats

#categoric fitur dan continuous fiture

class CategoricalFeature():
    def __init__(self, df, feature):
        self.df = df
        self.feature = feature

    @property
    def df_lite(self):
        df_lite = self.df
        df_lite['bin'] = df_lite[self.feature].fillna('MISSING')
        return df_lite[['bin', 'good_bad']]


class ContinuousFeature():
    def __init__(self, df, feature):
        self.df = df
        self.feature = feature
        self.bin_min_size = int(len(self.df) * 0.05)

    def __generate_bins(self, bins_num):
        df = self.df[[self.feature, 'good_bad']]
        df['bin'] = pd.qcut(df[self.feature], bins_num, duplicates='drop') \
                    .apply(lambda x: x.left) \
                    .astype(float)
        return df

    def __generate_correct_bins(self, bins_max=20):
        for bins_num in range(bins_max, 1, -1):
            df = self.__generate_bins(bins_num)
            df_grouped = pd.DataFrame(df.groupby('bin') \
                                      .agg({self.feature: 'count',
                                            'good_bad': 'sum'})) \
                                      .reset_index()
            r, p = stats.stats.spearmanr(df_grouped['bin'], df_grouped['good_bad'])

            if (
                    abs(r)==1 and                                                        # periksa apakah WOE untuk tiap bin adalah monotomic
                    df_grouped[self.feature].min() > self.bin_min_size                   # periksa apakah size setiap bin besar dari 5%
                    and not (df_grouped[self.feature] == df_grouped['good_bad']).any()      # periksa apakah label Yes dan No jumlahnya adalah 0
            ):
                break

        return df

    @property
    def df_lite(self):
        df_lite = self.__generate_correct_bins()
        df_lite['bin'].fillna('MISSING', inplace=True)
        return df_lite[['bin', 'good_bad']]

"""Information Value kita gunakan untuk menghitung seberapa penting dan prediktif terhadap target"""

# Information Value
pd.set_option('mode.chained_assignment', None)

class AttributeRelevance():
    def seq_palette(self, n_colors):
        return sns.cubehelix_palette(n_colors, start=.5, rot=-.75, reverse=True)

    def bulk_iv(self, feats, iv, woe_extremes=False):
        iv_dict = {}
        for f in feats:
            iv_df, iv_value = iv.calculate_iv(f)
            if woe_extremes:
                iv_dict[f.feature] = [iv_value, iv_df['woe'].min(), iv_df['woe'].max()]
                cols = ['iv', 'woe_min', 'woe_max']
            else:
                iv_dict[f.feature] = iv_value
                cols = ['iv']
        df = pd.DataFrame.from_dict(iv_dict, orient='index', columns=cols)
        return df

    def bulk_stats(self, feats, s):
        stats_dict = {}
        for f in feats:
            p_value, effect_size = s.calculate_chi(f)
            stats_dict[f.feature] = [p_value, effect_size]
        df = pd.DataFrame.from_dict(stats_dict, orient='index', columns=['p-value', 'effect_size'])
        return df

    def analyze(self, feats, iv, s=None, interpretation=False):
        df_iv = self.bulk_iv(feats, iv).sort_values(by='iv', ascending=False)
        if s is not None:
            df_stats = self.bulk_stats(feats, s)
            df_iv = df_iv.merge(df_stats, left_index=True, right_index=True)
        if interpretation:
            df_iv['iv_interpretation'] = df_iv['iv'].apply(iv.interpretation)
            if s is not None:
                df_iv['es_interpretation'] = df_iv['effect_size'].apply(s.interpretation)
        return df_iv

    def draw_iv(self, feats, iv):
        df = self.analyze(feats, iv)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=df.index, y='iv', data=df, palette=self.seq_palette(len(feats)))
        ax.set_title('IV values')
        plt.xticks(rotation=90)
        plt.show()

    def draw_woe_extremes(self, feats, iv):
        df = self.bulk_iv(feats, iv, woe_extremes=True).sort_values(by='iv', ascending=False)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=df.index, y='woe_min', data=df, palette=self.seq_palette(len(feats)))
        sns.barplot(x=df.index, y='woe_max', data=df, palette=self.seq_palette(len(feats)))
        ax.axhline(y=0, color='black', linewidth=1)
        ax.set_title('Range of WOE values')
        ax.set_ylabel('WOE')
        plt.xticks(rotation=90)
        plt.show()

    def draw_woe_multiplot(self, feats, iv):
        n = len(feats)
        nrows = int(np.ceil(n/3))
        fig, ax = plt.subplots(nrows=nrows, ncols=3, figsize=(15, nrows*4))
        for i in range(n):
            iv_df, iv_value = iv.calculate_iv(feats[i])
            sns.barplot(x=feats[i].feature, y='woe', data=iv_df, color='#455872', ax=fig.axes[i])

        for ax in fig.axes:
            plt.sca(ax)
            plt.xticks(rotation=50)

        plt.tight_layout()
        plt.show()

class Analysis():
    def seq_palette(self, n_colors):
        return sns.cubehelix_palette(n_colors, start=.5, rot=-.75, reverse=True)

    def group_by_feature(self, feat):
        df = feat.df_lite \
                            .groupby('bin') \
                            .agg({'good_bad': ['count', 'sum']}) \
                            .reset_index()
        df.columns = [feat.feature, 'count', 'good']
        df['bad'] = df['count'] - df['good']
        return df

class StatsSignificance(Analysis):
    def calculate_chi(self, feat):
        df = self.group_by_feature(feat)
        df_chi = np.array(df[['good', 'bad']])
        n = df['count'].sum()

        chi = stats.chi2_contingency(df_chi)
        cramers_v = np.sqrt(chi[0] / n)          # assume that k=2 (good, bad)
        return chi[1], cramers_v

    @staticmethod
    def interpretation(cramers_v):
        if cramers_v < 0.1:
            return 'useless'
        elif cramers_v < 0.2:
            return 'weak'
        elif cramers_v < 0.4:
            return 'medium'
        elif cramers_v < 0.6:
            return 'strong'
        else:
            return 'very strong'

    def interpret_chi(self, feat):
        _, cramers_v = self.calculate_chi(feat)
        return self.interpretation(cramers_v)

    def print_chi(self, feat):
        p_value, cramers_v = self.calculate_chi(feat)
        print('P-value: %0.2f\nEffect size: %0.2f' % (p_value, cramers_v))
        print('%s is a %s predictor' % (feat.feature.capitalize(), self.interpretation(cramers_v)))


class IV(Analysis):
    @staticmethod
    def __perc_share(df, group_name):
        return df[group_name] / df[group_name].sum()

    def __calculate_perc_share(self, feat):
        df = self.group_by_feature(feat)
        df['perc_good'] = self.__perc_share(df, 'good')
        df['perc_bad'] = self.__perc_share(df, 'bad')
        df['perc_diff'] = df['perc_good'] - df['perc_bad']
        return df

    def __calculate_woe(self, feat):
        df = self.__calculate_perc_share(feat)
        df['woe'] = np.log(df['perc_good']/df['perc_bad'])
        df['woe'] = df['woe'].replace([np.inf, -np.inf], np.nan).fillna(0)
        return df

    def calculate_iv(self, feat):
        df = self.__calculate_woe(feat)
        df['iv'] = df['perc_diff'] * df['woe']
        return df, df['iv'].sum()

    def draw_woe(self, feat):
        iv_df, iv_value = self.calculate_iv(feat)
        fig, ax = plt.subplots(figsize=(10,6))
        sns.barplot(x=feat.feature, y='woe', data=iv_df, palette=self.seq_palette(len(iv_df.index)))
        ax.set_title('WOE visualization for: ' + feat.feature)
        plt.show()
        plt.show()

    @staticmethod
    def interpretation(iv):
        if iv < 0.02:
            return 'useless'
        elif iv < 0.1:
            return 'weak'
        elif iv < 0.3:
            return 'medium'
        elif iv < 0.5:
            return 'strong'
        else:
            return 'suspicious'

    def interpret_iv(self, feat):
        _, iv = self.calculate_iv(feat)
        return self.interpretation(iv)

    def print_iv(self, feat):
        _, iv = self.calculate_iv(feat)
        print('Information value: %0.2f' % iv)
        print('%s is a %s predictor' % (feat.feature.capitalize(), self.interpretation(iv)))

from pandas.core.dtypes.common import is_numeric_dtype
#selection feat
feats_dict = {}

for col in [c for c in df.columns if c != 'good_bad']:
  if is_numeric_dtype(df[col]):
    feats_dict[col] = ContinuousFeature(df,col)
  else :
    feats_dict[col] = CategoricalFeature(df,col)

feats = list(feats_dict.values())

iv = IV()
s = StatsSignificance()

ar = AttributeRelevance()


df_analysis = ar.analyze(feats, iv, s, interpretation=True)
display(df_analysis)

df_analysis_sign = df_analysis[df_analysis['p-value']<0.05]

fig, ax = plt.subplots(figsize=(10,6))
sns.regplot(x='iv', y='effect_size', data=df_analysis_sign, color='#455872')
ax.set_title('Information value vs effect size')
plt.show()

print('Pearson correlation: %0.2f' % df_analysis_sign['iv'].corr(df_analysis_sign['effect_size']))
print('Spearman correlation: %0.2f' % df_analysis_sign['iv'].corr(df_analysis_sign['effect_size'], method='spearman'))

ar.draw_iv(feats, iv)

ar.draw_woe_multiplot(feats,iv)

#select fitur
feature_keep = df_analysis[df_analysis["iv"] > 0.01].index
feature_keep

feature_keep = ['last_pymnt_amnt', 'total_rec_prncp', 'total_pymnt_inv', 'total_pymnt',
       'sub_grade', 'grade', 'int_rate', 'term', 'dti', 'revol_util',
       'annual_inc', 'inq_last_6mths', 'verification_status', 'purpose',
       'total_rec_int', 'funded_amnt', 'loan_amnt', 'funded_amnt_inv',
       'home_ownership', 'installment','good_bad']

#for splitting
df = df[feature_keep]

#check correlation
fig = plt.figure(figsize = (20,20))
matrix = np.triu(df.corr())
sns.heatmap(df.corr(), center = 0,
           fmt='.3f', square = True,
           annot = True, linewidth = 0.3, mask = matrix)
plt.show()

#make a binning data 
target = "good_bad"
bins = sc.woebin(df,target,monotonic_trend="auto_asc_desc")

sc.woebin_plot(bins)

def woebin_plot_new(bins, x=None, title=None, show_iv=True):
    
    xs = x
    # bins concat 
    if isinstance(bins, dict):
        bins = pd.concat(bins, ignore_index=True)
    # good bad distr
    def gb_distr(binx):
        binx['good_distr'] = binx['good']/sum(binx['count'])
        binx['bad_distr'] = binx['bad']/sum(binx['count'])
        return binx
    bins = bins.groupby('variable').apply(gb_distr)
    # x variable names
    if xs is None: xs = bins['variable'].unique()
    # plot export
    plotlist = {}
    for i in xs:
        binx = bins[bins['variable'] == i].reset_index()
        plotlist[i] = plot_bin_new(binx, title, show_iv)
    return plotlist

def plot_bin_new(binx, title, show_iv):
  
    # y_right_max
    y_right_max = np.ceil(binx['badprob'].max()*10)
    if y_right_max % 2 == 1: y_right_max=y_right_max+1
    if y_right_max - binx['badprob'].max()*10 <= 0.3: y_right_max = y_right_max+2
    y_right_max = y_right_max/10
    if y_right_max>1 or y_right_max<=0 or y_right_max is np.nan or y_right_max is None: y_right_max=1
    ## y_left_max
    y_left_max = np.ceil(binx['count_distr'].max()*10)/10
    if y_left_max>1 or y_left_max<=0 or y_left_max is np.nan or y_left_max is None: y_left_max=1
    # title
    title_string = binx.loc[0,'variable']+"  (iv:"+str(round(binx.loc[0,'total_iv'],4))+")" if show_iv else binx.loc[0,'variable']
    title_string = title+'-'+title_string if title is not None else title_string
    # param
    ind = np.arange(len(binx.index))    # the x locations for the groups
    width = 0.5       # the width of the bars: can also be len(x) sequence
    ###### plot ###### 
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax2 = ax1.twinx()
    # ax1
    p1 = ax1.bar(ind, binx['good_distr'], width, color=(24/254, 192/254, 196/254))
    p2 = ax1.bar(ind, binx['bad_distr'], width, bottom=binx['good_distr'], color=(246/254, 115/254, 109/254))
    for i in ind:
        ax1.text(i, binx.loc[i,'count_distr']*1.02, str(round(binx.loc[i,'count_distr']*100,1))+'%, '+str(binx.loc[i,'count']), ha='center')
    # ax2
    ax2.plot(ind, binx['badprob'], marker='o', color='blue')
    for i in ind:
        ax2.text(i, binx.loc[i,'badprob']*1.02, str(round(binx.loc[i,'badprob'], 2)) , color='blue', ha='center')
    # settings
    ax1.set_ylabel('Bin count distribution')
    ax2.set_ylabel('Bad Probability', color='blue')
    ax1.set_yticks(np.arange(0, y_left_max+0.2, 0.2))
    ax2.set_yticks(np.arange(0, y_right_max+0.2, 0.2))
    ax2.tick_params(axis='y', colors='blue')
    ax1.tick_params(axis='x', rotation=45)
    plt.xticks(ind, binx['bin'])
#     plt.xticks(rotation = 45)
#     plt.figure(figsize=(12,6))
    plt.rcParams['font.size'] = '14'
    plt.title(title_string, loc='left')
    plt.legend((p2[0], p1[0]), ('bad', 'good'), loc='upper right')
    # show plot 
    # plt.show()
    return fig

woebin_plot_new(bins)

#backup data
data = df.copy()

#save
#data.to_csv("dataloan.csv")

#transsform to woe
df = sc.woebin_ply(df, bins)

"""### EDA base on Feature have high IV"""

plt.figure(figsize=(9,7),dpi=100)
sns.countplot(data=data,x='home_ownership',order=['MORTGAGE','RENT','OWN','OTHER'])
plt.title("Count Home Ownership")

"""nasabah peminjam paling banyak berstatus **MORTGAGE dan RENT**"""

home_owner_group = data.groupby("home_ownership",as_index=False)["good_bad"].mean()

plt.figure(figsize=(9,7))
sns.barplot(data=home_owner_group,x="home_ownership",y="good_bad",palette="magma",order=["MORTGAGE","OWN","RENT","OTHER"])
plt.title("% Good Borrower By Category Home Owner")
plt.xlabel("Home Ownerhip")
plt.ylabel("% Good Borrower");

"""Terlihat persentase dari **good borrower**, persentase tertinggi dimiliki **MORTGAGE** kemudian **OWN**, sedangkan persentase terendah yaitu **OTHER**. dari hal ini ketika nasabah memiliki status home ownership **OTHER** perlu untuk diawasi ketika melakukan pengajuan pinjaman"""

plt.figure(figsize=(9,7),dpi=100)
sns.countplot(data=data,y='purpose',order=data["purpose"].value_counts().index)

"""Berdasarkan purpose of borrower melakukan pinjaman untuk melunasi hutang dan melakukan credit card"""

data.groupby("purpose").agg({"good_bad":[len,'sum','mean']}).sort_values(('good_bad', 'mean'),ascending=False)

purpose_type = data.groupby("purpose",as_index=False)["good_bad"].mean().sort_values("good_bad",ascending=False)

plt.figure(figsize=(9,7))
sns.barplot(data=purpose_type,y="purpose",x="good_bad",palette="magma")
plt.title("Good Borrower By Purpose Type (%)")
plt.xlabel("Purpose")
plt.ylabel("Good Borrower(%)");

"""Borrower yang memiliki tujuan untuk **car,wedding dan major purchase** memiliki peluang yang tinggi untuk melakukan pelunasan, sedangkan nasabah dengan tujuan untuk **educational dan small_business** memiliki persentase yang paling rendah sehingga perlu adanya tindakan khusus untuk nasabah yang memiliki tujuan tersebut."""

plt.figure(figsize=(9,7),dpi=100)
sns.histplot(data=data,x='last_pymnt_amnt',hue='good_bad',kde=True,alpha=0.6)
plt.title("Distribution Last Payment Amount by Good and Bad Borrower")

"""Nasabah yang tidak mampu mengembalikkan uang pinjaman karena memiliki last payment yang rendah. """

data.groupby("grade")["good_bad"].mean().plot(kind="bar")
plt.axhline(y=0.7,linestyle="--",color="r")
plt.xticks(rotation=0);

"""Berdasarkan kategory grade, grade A,B dan C adalah kategory bagus karena memiliki persentase **Good Borrower** karena memiliki peluan untuk pelunasan uang pinjaman diatas 70%"""

data.groupby("grade").median().T

plt.figure(figsize=(9,7),dpi=100)
data.groupby("term")["good_bad"].mean().plot(kind="bar")
plt.title("Good Borrower by Term (%)")
plt.xlabel("Term")
plt.xticks(rotation=0)
plt.ylabel("Good Borrower (%)")

"""Nasabah dengan masa waktu 36 bulan memiliki prosentase pelunasan lebih tinggi dibandingkan dengan nasabah yang melakukan peminjaman dengan jangka waktu 60 bulan, sehingga diperlukan pengawasan khusus untuk peminjaman dengan jangka waktu lebih dari 36 bulan"""

data.groupby("term").median().T

plt.figure(figsize=(9,7),dpi=100)
sns.histplot(data=data,x='total_pymnt_inv',hue='good_bad')
plt.axvline(x=4000,color='r',linestyle="--")
plt.title("Distribution total payment invest by Good and Bad Borrower");

"""distribusi total payment invest dari **bad dan good borrower**, diatas 4000 dan semakin besarnya total payment maka invest frekuensi **bad borrower** semakin kecil"""

plt.figure(figsize=(9,7))
sns.boxplot(data=data,x='good_bad',y='int_rate')
plt.title('Boxplot Interest Rate')

"""interval interest rate **bad borrower** lebih besar daripada dengan **good borrower**"""

sns.pairplot(data,hue="good_bad")

"""# Preprocessing"""

#transsform to woe
df = sc.woebin_ply(df, bins)

fig = plt.figure(figsize = (20,20))
matrix = np.triu(df.corr())
sns.heatmap(df.corr(), center = 0,
           fmt='.3f', square = True,
           annot = True, linewidth = 0.3, mask = matrix)
plt.show()

# Model Building
"""

X = df.drop("good_bad",axis=1).copy()
y = df['good_bad'].copy()


X_train,X_test,y_train,y_test = train_test_split(X,y,stratify=y,test_size=0.3,random_state=42)

X_train.shape

logreg = LogisticRegression()
logreg.fit(X_train,y_train)

preds = logreg.predict(X_train)

accuracy = accuracy_score(preds,y_train)
print(accuracy)

preds_test = logreg.predict(X_test)

accuracy = accuracy_score(preds_test,y_test)
print(accuracy)

false_positive_rate, true_positive_rate, threshold = roc_curve(y_train,logreg.predict_proba(X_train)[:,1])
roc_auc_value = roc_auc_score(y_train, logreg.predict_proba(X_train)[:,1]).round(4)
gini_value = ((2*roc_auc_value)-1).round(4)

print('AUC for Logistic Regression on val data: ', round(roc_auc_value*100, 2), '%')
print('Gini for Logistic Regression on val data: ', round(gini_value*100, 2), '%')

false_positive_rate, true_positive_rate, threshold = roc_curve(y_test,logreg.predict_proba(X_test)[:,1])
roc_auc_value = roc_auc_score(y_test, logreg.predict_proba(X_test)[:,1]).round(4)
gini_value = ((2*roc_auc_value)-1).round(4)

print('AUC for Logistic Regression on val data: ', round(roc_auc_value*100, 2), '%')
print('Gini for Logistic Regression on val data: ', round(gini_value*100, 2), '%')

y_train_pred = logreg.predict(X_train)
cnf_matrix = metrics.confusion_matrix(y_train, y_train_pred)
print(metrics.classification_report(y_train, y_train_pred))
sns.heatmap(cnf_matrix,cmap='coolwarm_r',annot=True,linewidth=0.5,fmt='d')
plt.title('Confusion Matrix')
plt.xlabel('Prediksi')
plt.ylabel('Realita')

y_test_pred = logreg.predict(X_test)
cnf_matrix = metrics.confusion_matrix(y_test, y_test_pred)
print(metrics.classification_report(y_test,y_test_pred))
sns.heatmap(cnf_matrix,cmap='coolwarm_r',annot=True,linewidth=0.5,fmt='d')
plt.title('Confusion Matrix')
plt.xlabel('Prediksi')
plt.ylabel('Realita')

#recursive Elimination
from sklearn.feature_selection import RFE
model = LogisticRegression(solver='lbfgs', max_iter=500)
rfe = RFE(model)
rfe = rfe.fit(X_train, y_train)

X_train.columns[rfe.support_]

X_train_new = X_train[X_train.columns[rfe.support_]]
X_test_new = X_test[X_test.columns[rfe.support_]]

fig = plt.figure(figsize = (20,20))
matrix = np.triu(X_train_new.corr())
sns.heatmap(X_train_new.corr(), center = 0,
           fmt='.3f', square = True,
           annot = True, linewidth = 0.3, mask = matrix)
plt.show()

#seperti yang terlihat pada heatmap ada fitur yang berkolerasi diatas 0.95
#fitur yang di take out ada fitur yang memiliki nilai IV terendah

drop_feat = ["total_pymnt_inv_woe","funded_amnt_inv_woe"]


X_train_new = X_train_new.drop(drop_feat,axis=1)
X_test_new = X_test_new.drop(drop_feat,axis=1)

param_grid = {"penalty": ["l1","l2"],
             'C' : [1.0,2.0,3.0],
             'max_iter':[100,200,300,500],
             'solver' : ['newton-cg','lbfgs','sag','saga','liblinear'],
             }

model = LogisticRegression()#class_weight="balanced")
grid_search = RandomizedSearchCV(model,param_grid,cv=5)
grid_search.fit(X_train_new,y_train)

grid_search.best_params_

y_train_pred = grid_search.best_estimator_.predict(X_train_new)
y_test_pred = grid_search.best_estimator_.predict(X_test_new)

false_positive_rate, true_positive_rate, threshold = roc_curve(y_train,grid_search.predict_proba(X_train_new)[:,1])
roc_auc_value = roc_auc_score(y_train, grid_search.predict_proba(X_train_new)[:,1]).round(4)
gini_value = ((2*roc_auc_value)-1).round(4)

print('AUC for Logistic Regression on val data: ', round(roc_auc_value*100, 2), '%')
print('Gini for Logistic Regression on val data: ', round(gini_value*100, 2), '%')

fig, ax = plt.subplots(1, figsize=(8,6))
plt.title('Receiver Operating Characteristic - LogReg Classifier training')
plt.plot(false_positive_rate, true_positive_rate)
plt.plot([0, 1], ls="--")
plt.plot([0, 0], [1, 0] , c=".7"), plt.plot([1, 1] , c=".7")
plt.ylabel('True Positive Rate')
plt.xlabel('False Positive Rate')

plt.text(ax.get_xlim()[1]*6/10, 
         0, 
         f"""\n
         AUC score: {round(roc_auc_value*100, 2)} %
         Gini index: {round(gini_value*100, 2)} %
         """)

plt.show()

false_positive_rate, true_positive_rate, threshold = roc_curve(y_test,grid_search.predict_proba(X_test_new)[:,1])
roc_auc_value = roc_auc_score(y_test, grid_search.predict_proba(X_test_new)[:,1]).round(4)
gini_value = ((2*roc_auc_value)-1).round(4)

print('AUC for Logistic Regression on val data: ', round(roc_auc_value*100, 2), '%')
print('Gini for Logistic Regression on val data: ', round(gini_value*100, 2), '%')

fig, ax = plt.subplots(1, figsize=(8,6))
plt.title('Receiver Operating Characteristic - LogReg Classifier test')
plt.plot(false_positive_rate, true_positive_rate)
plt.plot([0, 1], ls="--")
plt.plot([0, 0], [1, 0] , c=".7"), plt.plot([1, 1] , c=".7")
plt.ylabel('True Positive Rate')
plt.xlabel('False Positive Rate')

plt.text(ax.get_xlim()[1]*6/10, 
         0, 
         f"""\n
         AUC score: {round(roc_auc_value*100, 2)} %
         Gini index: {round(gini_value*100, 2)} %
         """)

plt.show()

y_train_pred = grid_search.predict(X_train_new)
cnf_matrix = metrics.confusion_matrix(y_train, y_train_pred)
print(metrics.classification_report(y_train, y_train_pred))
sns.heatmap(cnf_matrix,cmap='coolwarm_r',annot=True,linewidth=0.5,fmt='d')
plt.title('Confusion Matrix')
plt.xlabel('Prediksi')
plt.ylabel('Realita')

y_test_pred = grid_search.predict(X_test_new)
cnf_matrix = metrics.confusion_matrix(y_test, y_test_pred)
print(metrics.classification_report(y_test,y_test_pred))
sns.heatmap(cnf_matrix,cmap='coolwarm_r',annot=True,linewidth=0.5,fmt='d')
plt.title('Confusion Matrix')
plt.xlabel('Prediksi')
plt.ylabel('Realita')

"""Dari hasil model, terlihat bahwa Bad borrower masih cukup banyak yang terhitung sebagai good borrowe sehingga kita perlu menurunkan hal ini, dengan cara mencari cut proba terbaik untuk meningkatkan recall dari model

# Cut Off
"""

data_train = pd.DataFrame()
data_test = pd.DataFrame()

data_train["proba"] = grid_search.predict_proba(X_train_new)[:,1]
data_test["proba"] = grid_search.predict_proba(X_test_new)[:,1]

data_train["label"] = pd.DataFrame(y_train).reset_index(drop=True)
data_test["label"] = pd.DataFrame(y_test).reset_index(drop=True)

data_test_split_proba = data_test[['label', 'proba']]
data_test_split_proba['bins'] = pd.qcut(data_test_split_proba['proba'], q=8)
#data_test_split_proba['bins'] = pd.cut(data_test_split_proba['proba'], bins=[0.010499999999999999, 0.085, 0.188, 0.331, 0.4,0.548, 0.943])
data_test_split_proba.head()

cnt_per_bin2 = data_test_split_proba.bins.value_counts().to_frame().reset_index().rename(columns={'bins':'cnt_debtors'}).sort_values('index')
cnt_per_bin2.head()

bad_per_bin2 = data_test_split_proba.groupby(['bins','label']).count().reset_index().rename(columns={'proba':'cnt_bad_debtors'})
bad_per_bin2 = bad_per_bin2[bad_per_bin2['label']==0]
bad_per_bin2.head()

summary2 = bad_per_bin2.merge(cnt_per_bin2, how='inner', right_on='index', left_on='bins')
summary2['pct_bad_average'] = round((summary2['cnt_bad_debtors'] / summary2['cnt_debtors'])*100 , 2)
summary2.head()

summary2['bins'] = summary2.bins.astype(str)
plt.figure(figsize=(12,9))
sns.lineplot(data = summary2, x='bins', y='pct_bad_average')
plt.xticks(rotation=45)
plt.ylabel('% average_good')
plt.title("Trend Average Bad Borrower Rate tiap Binning untuk Data Test", size=16)
# label points on the plot
for x, y in zip(summary2['bins'], summary2['pct_bad_average']):# the position of the data label relative to the data point can be adjusted by adding/subtracting a value from the x &/ y coordinates
    plt.text(x = x, # x-coordinate position of data label
             y = y+0.001,
             s = '{:.2f}'.format(y), # data label, formatted to ignore decimals
             color = 'black') # set colour of line# y

tr = 0.91388
y_train_pred = np.where(grid_search.predict_proba(X_train_new)[:,1]> tr,1,0)
cnf_matrix = metrics.confusion_matrix(y_train, y_train_pred)
print(metrics.classification_report(y_train, y_train_pred))
sns.heatmap(cnf_matrix,cmap='coolwarm_r',annot=True,linewidth=0.5,fmt='d')
plt.title('Confusion Matrix')
plt.xlabel('Prediksi')
plt.ylabel('Realita')

tr = 0.91388
y_test_pred = np.where(grid_search.predict_proba(X_test_new)[:,1]> tr,1,0)
cnf_matrix = metrics.confusion_matrix(y_test, y_test_pred)
print(metrics.classification_report(y_test,y_test_pred))
sns.heatmap(cnf_matrix,cmap='coolwarm_r',annot=True,linewidth=0.5,fmt='d')
plt.title('Confusion Matrix')
plt.xlabel('Prediksi')
plt.ylabel('Realita')

"""dengan mengambil titik cut off proba di 0.777, model telah berhasil menurukan nilai dari bad borrower yang terhitung sebagai good borrower dengan sangat baik. hal ini sangat diperlukan mengingat ketika perusahaan telah memiliki nama yang besar maka akan banyak orang yang akan melakukan peminjaman pada perusahaan tersebut jadi kita memerlukan ML yang sangat baik untuk dapat memisahkan mana peminjam yang **Good** dan **Bad** dengan sangat baik"""

fig, ax = plt.subplots(figsize=(12,3))
sns.histplot(x=grid_search.predict_proba(X_train_new)[:,1],
             binwidth=0.025,
             kde=True,
             ax=ax)

ax.set_title('Logreg Proba Training')
ax.set_xlabel('Prediction Probability')
ax.set_xlim(0,1)

fig, ax = plt.subplots(figsize=(12,3))
sns.histplot(x=grid_search.predict_proba(X_test_new)[:,1],
             binwidth=0.025,
             kde=True,
             ax=ax)

ax.set_title('Logreg Proba Testing')
ax.set_xlabel('Prediction Probability')
ax.set_xlim(0,1)

"""### Random Forest"""

from sklearn.ensemble import RandomForestClassifier
rfc = RandomForestClassifier()
rfc.fit(X_train, y_train)

rfc_pred_train = rfc.predict(X_train)
rfc_pred_test = rfc.predict(X_test)

from sklearn.metrics import classification_report, confusion_matrix
print(classification_report(y_train,rfc_pred_train))
sns.heatmap(cnf_matrix,cmap='coolwarm_r',annot=True,linewidth=0.5,fmt='d')
plt.title('Confusion Matrix')
plt.xlabel('Prediksi')
plt.ylabel('Realita')

print(classification_report(y_test,rfc_pred_test))
sns.heatmap(cnf_matrix,cmap='coolwarm_r',annot=True,linewidth=0.5,fmt='d')
plt.title('Confusion Matrix')
plt.xlabel('Prediksi')
plt.ylabel('Realita')