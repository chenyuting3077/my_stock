from bokeh.models import ColumnDataSource

my_api_key = "82561f5b58384ea3978bcd6117f5bb1e"
WIDTH_PLOT = 1500
# 股票種類
stock_code = ["GOOG", "AAPL", "MSFT"]

stock = ColumnDataSource(
    data=dict(date=[], open=[], close=[], high=[], volumn=[], Status=[]))


# ========================= callback_function ===========================#
def dropdown_on_change(attrname, old, new):
    update(new)
    # print(stock.data["close"])


# ========================= update ===========================#
def update(selected="GOOG"):
    import pandas as pd
    td = TDClient(my_api_key)
    df_stock = td.time_series(symbol=selected,
                              interval="1day"
                              ).as_pandas()

    def incr_decr(c, o):
        if c > o:
            value = 'Increase'
        elif c < o:
            value = 'Decrease'
        else:
            value = 'Equal'
        return value

    df_stock['Status'] = [incr_decr(c, o) for c, o in zip(df_stock.close, df_stock.open)]

    # 將 y 和 height 也分別新增一欄
    df_stock['Middle'] = (df_stock.close + df_stock.open) / 2
    df_stock['Height'] = abs(df_stock.close - df_stock.open)

    # 新增季線、5日線
    df_stock['SMA_5'] = df_stock['close'].rolling(5).mean()
    df_stock['SMA_10'] = df_stock['close'].rolling(10).mean()
    df_stock['SMA_50'] = df_stock['close'].rolling(50).mean()

    # 新增 畫橫線 所需使用東西
    df_stock["index_eq"] = pd.Series(df_stock.index[df_stock.Status == 'Equal'])
    df_stock["middle_eq"] = pd.Series(df_stock.Middle[df_stock.Status == 'Equal'])
    # # 新增 畫 K 線: Taiwan style
    df_stock["index_ic"] = pd.Series(df_stock.index[df_stock.Status == 'Increase'])
    df_stock["Middle_ic"] = pd.Series(df_stock.Middle[df_stock.Status == 'Increase'])
    df_stock["Height_ic"] = pd.Series(df_stock.Height[df_stock.Status == 'Increase'])

    df_stock["index_dc"] = pd.Series(df_stock.index[df_stock.Status == 'Decrease'])
    df_stock["Middle_dc"] = pd.Series(df_stock.Middle[df_stock.Status == 'Decrease'])
    df_stock["Height_dc"] = pd.Series(df_stock.Height[df_stock.Status == 'Decrease'])

    # 繪製長方體時 width 以毫秒 (ms) 為單位
    df_stock["hours_12"] = 12 * 60 * 60 * 1000

    stock.data = stock.from_df(df_stock)


# ========================= draw_on_web ===========================#
def create_input():
    from bokeh.models import Select

    # 選擇股票
    select = Select(title="Option:", value="foo", options=stock_code)
    select.on_change('value', dropdown_on_change)

    return select


def create_output():
    candle_figure = plot_stock_price()
    sma_figure = plot_sma()
    volume_figure = plot_volume()

    return column(candle_figure, sma_figure, volume_figure)


# ==========================plot figue===============================#
from bokeh.plotting import figure
from bokeh.palettes import Category20
from bokeh.models.widgets import PreText
from bokeh.models import BooleanFilter, CDSView, BoxAnnotation, Band, Span, Select, LinearAxis, DataRange1d, Range1d
from bokeh.models.formatters import PrintfTickFormatter, NumeralTickFormatter
from math import pi

WIDTH_PLOT = 1500

RED = Category20[7][6]
GREEN = Category20[5][4]

BLUE = Category20[3][0]
BLUE_LIGHT = Category20[3][1]

ORANGE = Category20[3][2]
PURPLE = Category20[9][8]
BROWN = Category20[11][10]

TOOLS = 'pan,wheel_zoom,reset'


def plot_stock_price():
    p = figure(x_axis_type="datetime", plot_width=WIDTH_PLOT, plot_height=400,
               title="Stock price + Bollinger Bands (2 std)",
               tools=TOOLS, toolbar_location='above')

    inc = stock.data['close'] > stock.data['open']
    dec = stock.data['open'] > stock.data['close']
    view_inc = CDSView(source=stock, filters=[BooleanFilter(inc)])
    view_dec = CDSView(source=stock, filters=[BooleanFilter(dec)])

    width = 35000000

    p.segment(x0='datetime', x1='datetime', y0='low', y1='high', color=RED, source=stock, view=view_inc)
    p.segment(x0='datetime', x1='datetime', y0='low', y1='high', color=GREEN, source=stock, view=view_dec)

    p.vbar(x='datetime', width=width, top='open', bottom='close', fill_color=RED, line_color=RED,
           source=stock,
           view=view_inc)
    p.vbar(x='datetime', width=width, top='open', bottom='close', fill_color=GREEN, line_color=GREEN,
           source=stock,
           view=view_dec)

    # p.line(x='date', y='close_line', line_width=1, color=BLUE, line_alpha=0.7, souce=stock)

    band = Band(base='date', lower='bolling_lower', upper='bolling_upper', source=stock, level='underlay',
                fill_alpha=0.5, line_width=1, line_color='black', fill_color=BLUE_LIGHT)
    p.add_layout(band)

    p.yaxis.formatter = NumeralTickFormatter(format='$ 0,0[.]000')

    return p


# Simple Moving Average
def plot_sma():
    p = figure(x_axis_type="datetime", plot_width=WIDTH_PLOT, plot_height=300,
               title="Simple Moving Average (press the legend to hide/show lines)", )

    p.line(x='datetime', y='SMA_5', line_width=2, color=BLUE, source=stock, legend='5 days', muted_color=BLUE,
           muted_alpha=0.2)
    p.line(x='datetime', y='SMA_10', line_width=2, color=ORANGE, source=stock, legend='10 days', muted_color=ORANGE,
           muted_alpha=0.2)
    p.line(x='datetime', y='SMA_50', line_width=2, color=PURPLE, source=stock, legend='50 days', muted_color=PURPLE,
           muted_alpha=0.2)

    p.legend.location = "bottom_left"
    p.legend.border_line_alpha = 0
    p.legend.background_fill_alpha = 0
    p.legend.click_policy = "mute"
    p.yaxis.formatter = NumeralTickFormatter(format='$ 0,0[.]000')

    return p


#### Volume line
def plot_volume():
    p = figure(x_axis_type="datetime", plot_width=WIDTH_PLOT, plot_height=200, title="Volume", tools=TOOLS,
               toolbar_location='above')

    # p.xaxis.major_label_orientation = pi / 4
    p.grid.grid_line_alpha = 0.3

    w = 12 * 60 * 60 * 1000  # half day in ms

    p.line(x='datetime', y='volume', line_width=2, color=BLUE, source=stock)
    p.vbar(x='datetime', width=w, top="volume", source=stock)

    return p


# =========================== main ================================#
# 不能宣告在 if main 裡面
from bokeh.io import curdoc
from twelvedata import TDClient
from bokeh.layouts import column

update()

output = create_output()
intput = create_input()

curdoc().add_root(column(intput, output))
curdoc().title = "霆的操盤中心"
