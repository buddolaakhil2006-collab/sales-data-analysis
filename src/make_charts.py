from pathlib import Path
import html
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "sales_clean.csv"
FIG = ROOT / "figures"

COLORS = ["#2457A7", "#E49B33", "#32866B", "#A34F6F", "#6D70B5"]

def svg_header(title, width=1000, height=560):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#ffffff"/>', f'<text x="{width/2}" y="42" text-anchor="middle" font-family="Arial" font-size="24" font-weight="700" fill="#172B4D">{html.escape(title)}</text>']

def text(x,y,s,size=14,anchor="middle",color="#425466",weight="400"):
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="Arial" font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(str(s))}</text>'

def bar_chart(series, title, ylabel, path, money=False, rotate=False):
    W,H=1000,560; L,R,T,B=95,35,85,120 if rotate else 90
    vals=series.astype(float); vmax=max(vals.max()*1.15,1); plotw=W-L-R; ploth=H-T-B
    out=svg_header(title,W,H)
    for i in range(6):
        y=T+ploth*i/5; v=vmax*(1-i/5)
        out += [f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="#e8edf2"/>', text(L-12,y+5,(f"${v:,.0f}" if money else f"{v:,.0f}"),12,"end")]
    bw=plotw/max(len(vals)*1.6,1); gap=(plotw-len(vals)*bw)/(len(vals)+1)
    for i,(lab,val) in enumerate(vals.items()):
        x=L+gap+(bw+gap)*i; h=val/vmax*ploth; y=T+ploth-h
        out += [f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="4" fill="{COLORS[i%len(COLORS)]}"/>',text(x+bw/2,y-8,(f"${val:,.0f}" if money else f"{val:,.0f}"),11),text(x+bw/2,H-B+22,lab,13)]
    out += [f'<line x1="{L}" y1="{T+ploth}" x2="{W-R}" y2="{T+ploth}" stroke="#64748b"/>',text(28,T+ploth/2,ylabel,14, "middle")]
    out.append('</svg>');path.write_text('\n'.join(out),encoding='utf-8')

def line_chart(series, title, path, money=True):
    W,H=1120,580; L,R,T,B=90,35,80,105; vals=series.astype(float); vmax=vals.max()*1.12; ymin=min(0,vals.min()*1.1); plw=W-L-R; plh=H-T-B
    out=svg_header(title,W,H)
    for i in range(6):
        y=T+plh*i/5; v=vmax-(vmax-ymin)*i/5
        out += [f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="#e8edf2"/>', text(L-12,y+5,(f"${v:,.0f}" if money else f"{v:,.0f}"),12,"end")]
    points=[]
    for i,(lab,val) in enumerate(vals.items()):
        x=L+plw*i/max(len(vals)-1,1); y=T+plh*(vmax-val)/(vmax-ymin); points.append((x,y))
        if i%3==0: out.append(text(x,H-B+22,str(lab),12))
    out.append('<polyline fill="none" stroke="#2457A7" stroke-width="3" points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in points)+'"/>')
    for x,y in points: out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#2457A7"/>')
    out += [f'<line x1="{L}" y1="{T+plh}" x2="{W-R}" y2="{T+plh}" stroke="#64748b"/>','</svg>'];path.write_text('\n'.join(out),encoding='utf-8')

def main():
    FIG.mkdir(parents=True,exist_ok=True); df=pd.read_csv(CLEAN,parse_dates=["order_date"])
    monthly=df.set_index("order_date").resample("MS").agg(sales=("sales","sum"),profit=("profit","sum"))
    category=df.groupby("category").agg(revenue=("sales","sum"),profit=("profit","sum")).sort_values("revenue",ascending=False)
    region=df.groupby("region")["sales"].sum().sort_values(ascending=False)
    month=df.groupby(df.order_date.dt.month)["sales"].mean().reindex(range(1,13))
    bar_chart(category.revenue,"Revenue by Product Category","Revenue ($)",FIG/"category_revenue.svg",True)
    bar_chart(category.profit,"Profit by Product Category","Profit ($)",FIG/"category_profit.svg",True)
    bar_chart(region,"Revenue by Region","Revenue ($)",FIG/"regional_revenue.svg",True)
    line_chart(monthly.sales,"Monthly Sales Revenue (Synthetic Data)",FIG/"monthly_revenue.svg",True)
    line_chart(month,"Average Order Revenue by Calendar Month",FIG/"seasonality.svg",True)
    print(f"Generated five SVG charts in {FIG}")

if __name__ == "__main__": main()

