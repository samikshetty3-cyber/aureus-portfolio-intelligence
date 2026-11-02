import io
import html
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

st.set_page_config(page_title="Aureus | Portfolio Intelligence", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
NAVY="#071426"; PANEL="#0D1D33"; GOLD="#D9B66F"; MUTED="#92A4BA"; WHITE="#F4F0E8"
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600&display=swap');
html,body,[class*="css"],.stApp {font-family:'DM Sans',sans-serif}
.stApp {background:linear-gradient(120deg,#071426 0%,#0a1b31 60%,#081526 100%)}
h1,h2,h3 {font-family:'Playfair Display',serif!important;letter-spacing:.01em}
h1 {font-size:3rem!important;color:#f4f0e8!important}
h2 {color:#f4f0e8!important}
[data-testid="stSidebar"] {background:#081324;border-right:1px solid #24344a}
[data-testid="stSidebar"] .stRadio label {padding:8px 0}
[data-testid="stMetric"] {background:#0d1d33;border:1px solid #273b51;border-radius:12px;padding:20px}
[data-testid="stMetricLabel"] {color:#92a4ba}
[data-testid="stMetricValue"] {color:#f4f0e8;font-family:'Playfair Display',serif;font-size:2rem}
.stButton>button[kind="primary"],.stDownloadButton>button {background:#d9b66f;color:#071426;border:0;border-radius:8px;font-weight:700}
.stButton>button:hover,.stDownloadButton>button:hover {background:#efd195;color:#071426}
[data-testid="stFileUploader"] {border:1px solid #344963;border-radius:12px;padding:12px}
hr {border-color:#263a51}
.eyebrow {font-size:.72rem;letter-spacing:.27em;color:#d9b66f;font-weight:700}
.subtitle {color:#92a4ba;font-size:1.02rem;margin-top:-.4rem}
.panel-note {border:1px solid #2c465e;background:#10273d;padding:16px;border-radius:10px;color:#c4d4e2}
.brand {font-family:'Playfair Display',serif;font-size:2.3rem;color:#d9b66f}
.small-brand {letter-spacing:.22em;font-size:.63rem;color:#92a4ba}
</style>''',unsafe_allow_html=True)

@st.cache_data
def samples():
    return pd.read_csv('data/sample_holdings.csv'), pd.read_csv('data/sample_prices.csv')

def validate_holdings(df):
    required=['ticker','shares','price']
    missing=[c for c in required if c not in df.columns]
    if missing: raise ValueError('Missing required columns: '+', '.join(missing))
    df=df.copy()
    df['ticker']=df['ticker'].astype(str).str.strip().str.upper()
    if df['ticker'].eq('').any() or df['ticker'].duplicated().any(): raise ValueError('Tickers must be nonempty and unique.')
    for c in ['shares','price']:
        df[c]=pd.to_numeric(df[c],errors='coerce')
        if not np.isfinite(df[c]).all() or (df[c]<0).any(): raise ValueError(f'{c} must contain nonnegative finite numbers.')
    if (df['price']<=0).any(): raise ValueError('Prices must be greater than zero.')
    if (df['shares']<=0).any(): raise ValueError('Shares must be greater than zero.')
    if len(df)>250: raise ValueError('Maximum 250 holdings.')
    for c,default in [('name','Unknown'),('asset_class','Unclassified'),('sector','Unclassified')]:
        if c not in df: df[c]=default
        df[c]=df[c].fillna(default).astype(str)
    df['market_value']=df.shares*df.price
    total=df.market_value.sum()
    if total<=0: raise ValueError('Portfolio value must be positive.')
    df['weight']=df.market_value/total
    return df.sort_values('market_value',ascending=False).reset_index(drop=True)

def validate_prices(df,tickers):
    if 'date' not in df: raise ValueError('Price history must include a date column.')
    missing=[t for t in tickers if t not in df.columns]
    if missing: raise ValueError('Missing price-history tickers: '+', '.join(missing))
    p=df.copy();p['date']=pd.to_datetime(p.date,errors='coerce')
    if p.date.isna().any() or p.date.duplicated().any(): raise ValueError('Dates must be valid and unique.')
    p=p.sort_values('date').set_index('date')[tickers].apply(pd.to_numeric,errors='coerce')
    if p.isna().any().any() or (p<=0).any().any() or not np.isfinite(p.to_numpy()).all(): raise ValueError('Historical prices must be positive finite numbers.')
    if len(p)<3: raise ValueError('Provide at least three price dates.')
    return p

def chart_layout(fig, height=340):
    fig.update_layout(height=height,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color=WHITE,family='DM Sans'),margin=dict(l=10,r=10,t=25,b=10),legend=dict(orientation='h',y=-.15),hoverlabel=dict(bgcolor=PANEL))
    fig.update_xaxes(gridcolor='#24344a',zerolinecolor='#24344a')
    fig.update_yaxes(gridcolor='#24344a',zerolinecolor='#24344a')
    return fig

def pdf_report(df,metrics,notes,data_label):
    buf=io.BytesIO();doc=SimpleDocTemplate(buf,pagesize=(612,792),leftMargin=42,rightMargin=42,topMargin=44,bottomMargin=44)
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BrandCustom',fontName='Helvetica-Bold',fontSize=25,textColor=colors.HexColor('#0d1d33'),spaceAfter=6))
    styles.add(ParagraphStyle(name='SubCustom',fontSize=10,textColor=colors.HexColor('#65758a'),spaceAfter=20))
    story=[Paragraph('AUREUS  /  PORTFOLIO INTELLIGENCE',styles['BrandCustom']),Paragraph('Advisor portfolio review  •  '+datetime.now().strftime('%Y-%m-%d')+'  •  '+html.escape(data_label),styles['SubCustom'])]
    story.append(Paragraph('Portfolio overview',styles['Heading2']))
    data=[['Metric','Value']]+[[str(k),str(v)] for k,v in metrics.items()]
    table=Table(data,colWidths=[265,245],repeatRows=1);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0d1d33')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f3f7')]),('BOTTOMPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9)]));story.append(table);story.append(Spacer(1,16))
    story.append(Paragraph('Holdings',styles['Heading2']))
    hd=[['Ticker','Asset class','Value','Weight']]+[[str(r.ticker),str(r.asset_class)[:24],f'${r.market_value:,.2f}',f'{r.weight:.1%}'] for r in df.itertuples()]
    ht=Table(hd,colWidths=[80,185,135,110],repeatRows=1);ht.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0d1d33')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f3f7')]),('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]));story.append(ht);story.append(Spacer(1,18))
    story.append(Paragraph('Advisor notes',styles['Heading2']));story.append(Paragraph(html.escape(notes or 'No notes provided.').replace('\n','<br/>'),styles['BodyText']));story.append(Spacer(1,22))
    story.append(Paragraph('Important: Educational analytical prototype. Values reflect uploaded prices; sample data are fictional. Historical metrics, when available, use periodic price returns, exclude distributions and transaction costs, and are not forecasts. Not investment, tax, or legal advice. Human review required.',styles['BodyText']))
    doc.build(story);return buf.getvalue()

with st.sidebar:
    st.markdown('<div class="brand">Aureus ✦</div><div class="small-brand">PORTFOLIO INTELLIGENCE</div>',unsafe_allow_html=True)
    st.write('')
    page=st.radio('WORKSPACE',['Overview','Portfolio X-Ray','Risk Intelligence','Advisor Reports','Methodology'],label_visibility='collapsed')
    st.divider()
    st.caption('INSTITUTIONAL ANALYTICS  /  DEMO')
    st.caption('No account or brokerage connection required.')

sample_h,sample_p=samples()
with st.sidebar.expander('Portfolio data',expanded=False):
    hfile=st.file_uploader('Upload holdings CSV',type='csv',key='holdings')
    st.download_button('Download holdings template',sample_h.head(0).to_csv(index=False),file_name='aureus_holdings_template.csv',mime='text/csv')
    pfile=st.file_uploader('Optional historical prices CSV',type='csv',key='prices')
    st.download_button('Download price-history example',sample_p.to_csv(index=False),file_name='aureus_sample_prices.csv',mime='text/csv')
try:
    raw=pd.read_csv(hfile) if hfile is not None else sample_h
    df=validate_holdings(raw)
except Exception as exc:
    st.error(f'Holdings validation error: {exc}');st.stop()
using_sample=hfile is None
history_label='Fictional demonstration data' if using_sample and pfile is None else 'User-supplied data'
prices=None
if pfile is not None:
    try: prices=validate_prices(pd.read_csv(pfile),df.ticker.tolist())
    except Exception as exc: st.warning(f'Historical prices not loaded: {exc}')
elif using_sample:
    prices=validate_prices(sample_p,df.ticker.tolist())

value=df.market_value.sum();hhi=float((df.weight**2).sum());effective=1/hhi;top=df.iloc[0]
metrics={'Portfolio market value':f'${value:,.2f}','Holdings':str(len(df)),'Largest position':f'{top.ticker} ({top.weight:.1%})','Concentration HHI':f'{hhi:.3f}','Effective number of holdings':f'{effective:.1f}'}
if page=='Overview':
    st.markdown('<div class="eyebrow">WEALTH MANAGEMENT  /  ANALYTICS</div>',unsafe_allow_html=True)
    st.title('Clarity for every portfolio.')
    st.markdown('<div class="subtitle">Portfolio intelligence, risk visibility, and advisor-ready reporting in one workspace.</div>',unsafe_allow_html=True)
else:
    st.markdown('<div class="eyebrow">AUREUS  /  INTELLIGENCE SUITE</div>',unsafe_allow_html=True)
    st.title(page)
st.write('')
if using_sample: st.info('DEMONSTRATION MODE — Fictional holdings and simulated price history. Not live market data.')
else: st.info('UPLOADED HOLDINGS — Values use your supplied prices, not verified live quotes. Historical analysis requires a separate price-history CSV.')

if page in ['Overview','Portfolio X-Ray']:
    a,b,c,d=st.columns(4)
    a.metric('PORTFOLIO VALUE',f'${value:,.0f}')
    b.metric('POSITIONS',len(df))
    c.metric('LARGEST POSITION',f'{top.weight:.1%}',top.ticker,delta_color='off')
    d.metric('EFFECTIVE HOLDINGS',f'{effective:.1f}',f'HHI {hhi:.3f}',delta_color='off')
    st.write('')
    left,right=st.columns([1,1])
    with left:
        st.subheader('Asset allocation')
        allocation=df.groupby('asset_class',as_index=False).market_value.sum()
        fig=go.Figure(go.Pie(labels=allocation.asset_class,values=allocation.market_value,hole=.67,marker=dict(colors=[GOLD,'#4f9ec0','#56b49d','#8494b8','#c77869','#b49bc6']),textinfo='percent',hovertemplate='%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>'))
        fig.update_layout(annotations=[dict(text='ALLOCATION',x=.5,y=.5,showarrow=False,font=dict(size=12,color=MUTED))]);st.plotly_chart(chart_layout(fig),use_container_width=True)
    with right:
        st.subheader('Largest positions')
        top10=df.head(10).sort_values('weight')
        fig=go.Figure(go.Bar(x=top10.weight*100,y=top10.ticker,orientation='h',marker_color=GOLD,hovertemplate='%{y}: %{x:.1f}%<extra></extra>'))
        fig.update_layout(xaxis_title='Portfolio weight (%)',yaxis_title='');st.plotly_chart(chart_layout(fig),use_container_width=True)
    st.subheader('Portfolio holdings')
    display=df[['ticker','name','asset_class','sector','shares','price','market_value','weight']].copy()
    st.dataframe(display,hide_index=True,use_container_width=True,column_config={'price':st.column_config.NumberColumn('Supplied price',format='$%.2f'),'market_value':st.column_config.NumberColumn('Market value',format='$%.2f'),'weight':st.column_config.ProgressColumn('Weight',min_value=0,max_value=1,format='%.1%%')})
    st.download_button('Export analyzed holdings',df.to_csv(index=False),file_name='aureus_portfolio_analysis.csv',mime='text/csv')
    if page=='Overview': st.caption('Explore Portfolio X-Ray, Risk Intelligence, and Advisor Reports from the sidebar.')

if page=='Risk Intelligence':
    st.subheader('Concentration diagnostics')
    a,b,c=st.columns(3)
    a.metric('TOP POSITION',f'{top.weight:.1%}')
    b.metric('TOP 3 COMBINED',f'{df.head(3).weight.sum():.1%}')
    c.metric('EFFECTIVE HOLDINGS',f'{effective:.1f}')
    alerts=[]
    if top.weight>.20: alerts.append(f'Largest holding ({top.ticker}) exceeds 20% of portfolio value.')
    if df.head(3).weight.sum()>.50: alerts.append('Top three holdings exceed 50% of portfolio value.')
    if effective<5: alerts.append('Concentration index implies fewer than five equally weighted effective positions.')
    if not alerts: st.success('No concentration thresholds triggered. This does not establish suitability or diversification adequacy.')
    for item in alerts: st.warning(item)
    st.caption('Thresholds are illustrative screening rules, not regulatory or suitability standards.')
    st.divider()
    st.subheader('Historical risk analysis')
    if prices is None:
        st.info('Upload a historical price CSV in the sidebar to enable returns, volatility, and drawdown. No synthetic history is generated for uploaded portfolios.')
    else:
        frequency=st.selectbox('Price observations',['Monthly','Daily','Weekly'],index=0 if using_sample and pfile is None else 1)
        annual={'Monthly':12,'Daily':252,'Weekly':52}[frequency]
        ret=prices.pct_change().dropna()
        w=df.set_index('ticker').loc[prices.columns,'weight'].to_numpy()
        # Constant-weight periodic rebalancing assumption; price-only returns exclude distributions.
        port=ret.dot(w)
        growth=(1+port).cumprod()
        drawdown=growth/growth.cummax()-1
        vol=float(port.std(ddof=1)*np.sqrt(annual)) if len(port)>1 else float('nan')
        maxdd=float(drawdown.min())
        r1,r2,r3=st.columns(3)
        r1.metric('ANNUALIZED VOLATILITY',f'{vol:.1%}')
        r2.metric('MAX DRAWDOWN',f'{maxdd:.1%}')
        r3.metric('OBSERVATIONS',len(prices))
        fig=go.Figure(go.Scatter(x=growth.index,y=growth.values,mode='lines',line=dict(color=GOLD,width=3),fill='tozeroy',fillcolor='rgba(217,182,111,.10)'))
        fig.update_layout(yaxis_title='Growth of $1 (price-only)');st.plotly_chart(chart_layout(fig),use_container_width=True)
        fig2=go.Figure(go.Scatter(x=drawdown.index,y=drawdown.values*100,mode='lines',line=dict(color='#d17d74',width=2),fill='tozeroy',fillcolor='rgba(209,125,116,.14)'))
        fig2.update_layout(yaxis_title='Drawdown (%)');st.plotly_chart(chart_layout(fig2,260),use_container_width=True)
        st.caption('Assumes constant portfolio weights rebalanced each observation. Uses price returns only (no dividends, fees, taxes, or cash flows). Frequency selection must match your CSV. Short histories yield unstable risk estimates.')
    st.divider()
    st.subheader('Illustrative one-period stress test')
    shock=st.slider('Uniform portfolio price shock (%)',min_value=-50,max_value=20,value=-15,step=1)
    st.metric('HYPOTHETICAL PORTFOLIO VALUE',f'${value*(1+shock/100):,.0f}',f'${value*shock/100:,.0f}',delta_color='off')
    st.caption('This is a uniform hypothetical price shock, not a historical scenario, prediction, or security-specific risk model.')

if page=='Advisor Reports':
    st.subheader('Client review briefing')
    st.markdown('<div class="panel-note">Prepare a portfolio overview for advisor review. All uploaded data remain within this app session; do not upload identifiable real-client information to this demonstration service.</div>',unsafe_allow_html=True)
    st.write('')
    st.write(f'**Market value:** ${value:,.2f}  ·  **Holdings:** {len(df)}  ·  **Largest holding:** {top.ticker} ({top.weight:.1%})')
    notes=st.text_area('Advisor notes (editable)',value=f'The largest holding is {top.ticker} at {top.weight:.1%} of reported market value. Review concentration, client objectives, liquidity needs, and investment constraints before making any recommendations.',height=150)
    pdf=pdf_report(df,metrics,notes,history_label)
    st.download_button('Download professional PDF report',pdf,file_name='Aureus_Advisor_Portfolio_Review.pdf',mime='application/pdf',type='primary')
    st.caption('PDF includes portfolio metrics, holdings, notes, and methodology limitations.')

if page=='Methodology':
    st.subheader('Transparent by design')
    st.markdown('''**Market value:** shares × user-supplied price.  
**Weight:** holding market value ÷ total portfolio value.  
**HHI:** sum of squared portfolio weights.  
**Effective holdings:** 1 ÷ HHI (concentration equivalent, not a measure of true independent risk).  
**Historical portfolio returns:** sum of each security’s price return × its portfolio weight, assuming rebalancing at each observation.  
**Annualized volatility:** standard deviation of periodic portfolio returns × square root of observations per year.  
**Maximum drawdown:** largest peak-to-trough decline in the constructed cumulative price-return series.  
**Stress test:** current portfolio value × (1 + chosen uniform percentage shock).''')
    st.divider()
    st.markdown('''**Limitations:** No live prices, automatic ETF look-through, benchmark feed, trading execution, tax optimization, or personal investment recommendations. Uploaded prices are not verified. Price-only history omits dividends and distributions. Simulated demonstration data are fictional. This prototype is not a production-grade advisory system and has not undergone a security or regulatory compliance audit.''')
    st.caption('Aureus · Research and educational prototype · Version 1.0')
