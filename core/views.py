from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import F, ExpressionWrapper, FloatField
import pandas as pd
import plotly.express as px
from django.http import HttpResponse
 
from .models import Venda

def login_view(request: HttpRequest):
    if request.method != 'POST':
        return render(request, 'login.html')

    email = request.POST['email']
    password = request.POST['password']
 
    try:
        user = User.objects.get(email=email)
        if not user.check_password(password):
            messages.error(request, 'Usuário ou senha inválidos.')
            return redirect('/')

        login(request, user)
        if user.is_superuser:
            return redirect('/diretoria/dashboard/')
                
        return redirect('/vendedor/dashboard/')
            
    except User.DoesNotExist:
        messages.error(request, 'Usuário ou senha inválidos.')
        redirect('/')
  
@login_required(login_url='/')
def vendedor_dashboard_view(request: HttpRequest):
    if request.user.is_superuser:
        return redirect('/diretoria/dashboard/')
    return render(request, 'vendedor-dashboard.html')

@login_required(login_url='/')
def diretoria_dashboard_view(request: HttpRequest):
    if not request.user.is_superuser:
        return redirect('/vendedor/dashboard')
 
    vendedor_filtro = request.GET.get('vendedor', 'todos')
 
    qs = Venda.objects.select_related('vendedor', 'produto').annotate(
        valor_total=ExpressionWrapper(
            F('produto__preco_final') * F('quantidade'),
            output_field=FloatField()
        ),
        lucro=ExpressionWrapper(
            (F('produto__preco_final') - F('produto__custo_compra')) * F('quantidade'),
            output_field=FloatField()
        ),
    )
    data = list(qs.values(
        'nome_cliente',
        'produto__nome',
        'quantidade',
        'valor_total',
        'lucro',
        'vendedor__id',
        'vendedor__username',
        'vendedor__first_name',
        'vendedor__last_name',
    ))
    df = pd.DataFrame(data)
 
    if df.empty:
        return render(request, 'diretoria-dashboard.html', {
            'grafico_qtd': '',
            'grafico_fat': '',
            'total_vendas': 0,
            'faturamento': '0,00',
            'lucro_total': '0,00',
            'vendedores': [],
            'vendedor_selecionado': 'todos',
        })
 
    df['vendedor_nome'] = df.apply(
        lambda r: (r['vendedor__first_name'] + ' ' + r['vendedor__last_name']).strip()
                or r['vendedor__username'],
        axis=1
    )    
    vendedores = df[['vendedor__id', 'vendedor_nome']].drop_duplicates().to_dict('records')
 
    df_f = df.copy()
    if vendedor_filtro != 'todos':
        try:
            df_f = df[df['vendedor__id'] == int(vendedor_filtro)]
        except ValueError:
            pass
 
    total_vendas = int(df_f['quantidade'].sum())
    faturamento  = float(df_f['valor_total'].sum())
    lucro_total  = float(df_f['lucro'].sum())
 
    # Gráfico 1
    df_qtd = (
        df_f.groupby('vendedor_nome', as_index=False)
        .size()
        .rename(columns={'size': 'num_vendas'})
        .sort_values('num_vendas', ascending=False)
    )
    fig_qtd = px.pie(
        df_qtd,
        names='vendedor_nome',
        values='num_vendas',
        title='Ranking de Vendedores (Nº de Vendas)',
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )
    fig_qtd.update_traces(
        textinfo = 'label+value'
    )
    fig_qtd.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Montserrat, sans-serif', color='#1e293b'),
        showlegend=True,
        height=360,
        margin=dict(t=50, b=20, l=20, r=20),
    )
 
    # Gráfico 2
    df_fat = (
        df_f.groupby('vendedor_nome', as_index=False)['valor_total']
        .sum()
        .sort_values('valor_total', ascending=False)
    )
    df_fat['valor_formatado'] = df_fat['valor_total'].apply(
        lambda v: f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    )

    fig_fat = px.bar(
        df_fat, x='vendedor_nome', y='valor_total',
        title='Faturamento por Vendedor (R$)',
        labels={'vendedor_nome': 'Vendedor', 'valor_total': 'Valor Total (R$)'},
        color='vendedor_nome',
        color_discrete_sequence=px.colors.sequential.Blues_r,
        text='valor_formatado', 
    )
    fig_fat.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Montserrat, sans-serif', color='#1e293b'),
        showlegend=False, coloraxis_showscale=False,
        margin=dict(t=50, b=40, l=40, r=20),
    )
 
    grafico_qtd = fig_qtd.to_html(full_html=False, include_plotlyjs='cdn',  config={'responsive': True})
    grafico_fat = fig_fat.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True})
 
    return render(request, 'diretoria-dashboard.html', {
        'grafico_qtd': grafico_qtd,
        'grafico_fat': grafico_fat,
        'total_vendas': total_vendas,
        'faturamento': f'{faturamento:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
        'lucro_total': f'{lucro_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
        'vendedores': vendedores,
        'vendedor_selecionado': vendedor_filtro,
    })
 
 
@login_required(login_url='/login/')
def exportar_excel(request: HttpRequest):
    return redirect('/diretoria/dashboard/')