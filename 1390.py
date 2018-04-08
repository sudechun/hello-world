from jqdata import *
import numpy as np
import pandas as pd
from datetime import *

def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    log.set_level('order', 'error')
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    g.chicangshu=10     #最大持仓股数量
    g.dapanindex='399006.XSHE'
    g.kongcangqi=context.current_dt
    g.blacklist=[]      #股票黑名单
    run_daily(rundaily_buy2, time='10:30', reference_security='000300.XSHG')
    run_daily(rundaily_sell, time='10:00', reference_security='000300.XSHG')
    run_monthly(runmonthly,monthday=1,time='night')
    runmonthly(context)
    
def rundaily_buy2(context):
    if context.current_dt<g.kongcangqi:
        return
    positions=context.portfolio.positions
    kemaishu=g.chicangshu-len(positions)    #今天剩余的可买股票数量
    codes=[]
    #g.stocks=list(set(g.stocks).difference(g.blacklist))  #剔除黑名单中的股票
    data=get_current_data()
    for k in g.stocks:
        if heitiane(context,k):
            continue
        if k in positions:
            continue
        if data[k].paused:
            continue
        codes.append(k)
    codes=codes[:g.chicangshu]
    if kemaishu>len(codes):
        kemaishu=len(codes)
    if kemaishu<=0:
        return        
    amount=context.portfolio.available_cash/kemaishu
    for i in range(kemaishu):
        s=codes[i]
        #log.info('买入股票%s，金额：%s',df.iloc[i][0], amount)
        order_value(s,amount)
        
def rundaily_sell(context):
    positions=context.portfolio.positions
    dpfx=context.current_dt<g.kongcangqi
    for k,p in positions.items():
        #yingli=(p.price-p.avg_cost)/p.avg_cost
        if dpfx==True :
            order_target(p.security, 0)
            #log.info('大盘有风险！卖出%s',p.security)
         
           
def runmonthly(context):
    #if context.current_dt.month%3 ==0:
    '''
    zs=['000001.XSHG','399006.XSHE']
    panel=get_price(zs,end_date=context.current_dt,count=30)
    df_close=panel['close']# 获取开盘价的[pandas.DataFrame],  行索引是[datetime.datetime]对象, 列索引是股票代号
    zs300,zs500=df_close[zs[0]],df_close[zs[1]]
    zf300=(zs300[-1]/zs300[0]-1)*100
    zf500=(zs500[-1]/zs500[0]-1)*100
    if zf300>zf500:
        g.stocks=check_stocks2(context)
    else:
    '''
    g.stocks=check_stocks(context)
    log.info('============更新股票池数量%s===========',len(g.stocks))

#防止黑天鹅函数    
def heitiane(context,stock):
    if stock.startswith('6'):
        index='000001.XSHG'
    else:
        index='399001.XSHE'
    nd1=get_bars(stock,2,include_now=True,unit='1d',fields=['close'])
    nd2=get_bars(index,2,include_now=True,unit='1d',fields=['close'])
    zf300=(nd1[-1][0]/nd1[0][0]-1)*100
    zf500=(nd2[-1][0]/nd2[0][0]-1)*100
    if zf300<-8 and zf500>-0.5:       #突然出现脱离大盘走势的暴跌，肯定有黑天鹅。
        return True
    else:
        return False
        
        
def before_trading_start(context):
    b=zhishuChuangyeban(context)
    send_message('美好的一天~%s'%b)

def zhishuChuangyeban(context):
    time=context.current_dt.strftime('%H:%M')
    if context.current_dt<g.kongcangqi:
        return True
    df=df_alldata()
    df5,df10,df20,df30,df50,df90=df[-5:],df[-10:],df[-20:],df[-30:],df[-50:],df[-90:]
    zf0=round((get_current_data()[g.dapanindex].last_price/df.iloc[-1,4]-1)*100,2)
    zf1=df.iloc[-1,7]
    zf5= round((df.iloc[-1,4]/df.iloc[-5- 1,4]-1)*100,2)
    zf10=round((df.iloc[-1,4]/df.iloc[-10-1,4]-1)*100,2)
    zf20=round((df.iloc[-1,4]/df.iloc[-20-1,4]-1)*100,2)
    zf30=round((df.iloc[-1,4]/df.iloc[-30-1,4]-1)*100,2)
    zf50=round((df.iloc[-1,4]/df.iloc[-50-1,4]-1)*100,2)
    zf90=round((df.iloc[-1,4]/df.iloc[-90-1,4]-1)*100,2)
    zf_5_10=round((df.iloc[-5,4]/df.iloc[-5-10-1,4]-1)*100,2)    #5天前的10天涨幅
    zf_10_20=round((df.iloc[-10,4]/df.iloc[-10-20-1,4]-1)*100,2) #10天前的20天涨幅
    ###半年的平均日成交金额/最近5日的平均日成交金额，如果绝对值>1.2,则为成交量异常！
    pre_syx_ratio=df.iloc[-2,8]   
    pre_xyx_ratio=df.iloc[-2,9]
    pre_st_ratio=df.iloc[-2,10]
    syx_ratio=df.iloc[-1,8]
    xyx_ratio=df.iloc[-1,9]
    st_ratio=df.iloc[-1,10]
    #log.info('st_ratio:%s,syx_ratio:%s,zf5:%s,zf20:%s',st_ratio,syx_ratio,zf5,zf20)
    if zf0<-2 and time>'11:00':     #下午跌幅超-2个点先回避一下   
        log.info('停：大盘午后跌幅超过-2%%')
        return True
    if zf10<-8 and -1<=zf1<=0:
        log.info('停：大盘出现10日暴跌中继！')
        g.kongcangqi=context.current_dt+timedelta(days=5+2)
        return True 
    if abs(pre_st_ratio)<=0.3 and abs(st_ratio)<=0.3 and -2<zf5<-0.5:
        log.info('停：大盘出现下跌途中的二个连续十字星，危险！')
        g.kongcangqi=context.current_dt+timedelta(days=5+2)
        return True 
    if syx_ratio>5 and zf1<-3 and zf10<-15:
        log.info('停：大盘出现下跌中5%%的长上影线')
        g.kongcangqi=context.current_dt+timedelta(days=5+1)
        return True        
    if syx_ratio>3 and zf10>10:
        log.info('停：大盘出现长上影线')
        g.kongcangqi=context.current_dt+timedelta(days=5+3)
        return True
    if abs(st_ratio)<=0.3 and zf1<1 and 5>zf5>=3 and zf10<8:
        g.kongcangqi=context.current_dt+timedelta(days=5+3)
        log.info('停：大盘出现5日高位十字星')
        return True
    if zf20>=7 and -1<zf5<1 and abs(st_ratio)<=0.3:
        log.info('停：大盘出现20日均线高位十字星')
        g.kongcangqi=context.current_dt+timedelta(days=5+3)
        return True
    if zf20<-10 and 0>zf5>-2:
        log.info('停：股灾！君子不立危墙之下！')
        g.kongcangqi=context.current_dt+timedelta(days=5+3)
        return True        
    if 1<zf20<3 and -1<zf5<1 and abs(st_ratio)<=0.3:
        log.info('停：大盘出现5日和20日死叉！')
        g.kongcangqi=context.current_dt+timedelta(days=5+3)
        return True 
    if zf50<40 and zf20>10 and -1<zf5<0  and st_ratio<-1.9:
        log.info('停：大盘出现20日高位圆弧顶！')
        g.kongcangqi=context.current_dt+timedelta(days=2)
        return True 
    if zf90<-9 and 3<zf50<5 and -2<zf20<-1  and abs(st_ratio)<=0.3:
        log.info('停：大盘出现90,50日下跌中继！')
        g.kongcangqi=context.current_dt+timedelta(days=56)
        return True          
    if zf30<-20 and zf10>20 and abs(st_ratio)<=0.3:
        log.info('停：大盘出现股灾暴跌下跌中继！')
        g.kongcangqi=context.current_dt+timedelta(days=8+3)
        return True         
    return False

## 选股函数中小盘
def check_stocks(context):
    security = get_index_stocks('000905.XSHG')
    q=query(valuation.code,valuation.market_cap,valuation.circulating_market_cap,valuation.turnover_ratio,valuation.pe_ratio,valuation.pb_ratio,indicator.inc_revenue_year_on_year,indicator.inc_operation_profit_year_on_year
            ).filter(valuation.code.in_(security),
            indicator.inc_operation_profit_year_on_year>50,
            valuation.turnover_ratio<=8,          #换手率>2%
            valuation.circulating_market_cap<=100,
            valuation.pe_ratio<50
            ).order_by(
                valuation.market_cap.asc()).limit(100) #desc
    df = get_fundamentals(q)
    Codes=list(df.code)
    '''
    for k in Codes:
        if heitiane(context,k)==True:
            g.blacklist.append(k)
    Codes=list(set(Codes).difference(g.blacklist))  #剔除黑名单中的股票
    '''
    #Codes=Codes[:10]
    return Codes 

#选择蓝筹股
def check_stocks2(context):
    security = get_index_stocks('000300.XSHG')
    q=query(valuation.code,valuation.market_cap,valuation.circulating_market_cap,valuation.turnover_ratio,valuation.pe_ratio,valuation.pb_ratio,income.total_operating_revenue,indicator.inc_operation_profit_year_on_year
            ).filter(valuation.code.in_(security),
            valuation.market_cap<=1000,
            valuation.market_cap>=500,
            valuation.pe_ratio<50
            ).order_by(
                valuation.market_cap.desc()).limit(100) #营业总收入
    df = get_fundamentals(q)
    Codes=list(df.code)
    #追涨策略
    ss=[]
    for k in Codes:
        nd=get_bars(k,20,include_now=True,unit='1d',fields=['date', 'open','high','low','close'])
        df=pd.DataFrame(nd,index=nd['date'])
        df['zf']=df['close'].pct_change()
        df['yx']=df.close>df.open           #是否收盘阳线
        zf10=(df.iloc[-1,4]/df.iloc[0,4]-1)*100
        df10=df[-5:]
        if len(df10[df10.zf>5])>=2: #10天内有8天以上收阳线
            ss.append(k)
    #ss=ss[:10]
    return ss 
    
def df_alldata():
    nd=get_bars(g.dapanindex,6*30,include_now=False,unit='1d',fields=['date', 'open','high','low','close','volume','money'])
    df1=pd.DataFrame(nd)
    df2=df1.copy()
    df2.index=df2.index+1
    #df1.drop([0],inplace=True)
    #df2.drop([len(df2)],inplace=True)
    #df1.index=df2.index
    f=lambda x,y:x if x>y else y    
    df1['zf']=(df1['close']/df2['close']-1)*100     
    df1['syx']=(df1['high']-df1.apply(lambda x:f(x.open,x.close),axis=1))/df2['close']*100
    df1['xyx']=(df1.apply(lambda x:(lambda x,y: x if x<y else y)(x.open,x.close),axis=1)-df1['low'])/df2['close']*100
    df1['st']=(df1.close-df1.open)/df2.close*100
    
    df1.zf=df1.zf.round(2)                  #索引为第7列，天涨幅
    df1.syx=df1.syx.round(2)                #第8列，上影线
    df1.xyx=df1.xyx.round(2)                #第9列，下影线
    df1.st=df1.st.round(2)                  #第10列，实体长度
    return df1
    
    
