from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import F, ExpressionWrapper, FloatField, Count
import pandas as pd
import plotly.express as px
from django.http import HttpResponse
 
from .models import Venda, Produto

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
        lucro_calc=ExpressionWrapper(
            (F('produto__preco_final') - F('produto__custo_compra')) * F('quantidade'),
            output_field=FloatField()
        ),
    )
    data = list(qs.values(
        'nome_cliente',
        'produto__nome',
        'quantidade',
        'valor_total',
        'lucro_calc',
        'vendedor__id',
        'vendedor__username',
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
            'page_obj': None,
        })
 
    df['vendedor_nome'] = df['vendedor__username'].fillna('').str.strip()

    vendedores = df[['vendedor__id', 'vendedor_nome']].drop_duplicates().to_dict('records')
 
    df_f = df.copy()
    if vendedor_filtro != 'todos':
        try:
            df_f = df[df['vendedor__id'] == int(vendedor_filtro)]
        except ValueError:
            pass
 
    total_vendas = int(df_f['quantidade'].sum())
    faturamento  = float(df_f['valor_total'].sum())
    lucro_total  = float(df_f['lucro_calc'].sum())
 
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
        textinfo='label+value'
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
 
    grafico_qtd = fig_qtd.to_html(full_html=False, include_plotlyjs='cdn', config={'responsive': True})
    grafico_fat = fig_fat.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True})

    if vendedor_filtro != 'todos':
        try:
            qs_hist = qs.filter(vendedor__id=int(vendedor_filtro))
        except ValueError:
            qs_hist = qs
    else:
        qs_hist = qs

    qs_hist = qs_hist.order_by('-criado_em')
    paginator = Paginator(qs_hist, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
 
    return render(request, 'diretoria-dashboard.html', {
        'grafico_qtd': grafico_qtd,
        'grafico_fat': grafico_fat,
        'total_vendas': total_vendas,
        'faturamento': f'{faturamento:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
        'lucro_total': f'{lucro_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
        'vendedores': vendedores,
        'vendedor_selecionado': vendedor_filtro,
        'page_obj': page_obj,
    })
 
@login_required(login_url='/login/')
def exportar_excel(request: HttpRequest):
    return redirect('/diretoria/dashboard/')

@login_required(login_url='/')
def vendedores_view(request: HttpRequest):
    if not request.user.is_superuser:
        return redirect('/vendedor/dashboard/')
    vendedores = User.objects.filter(is_superuser=False).annotate(
        total_vendas=Count('vendas')
    )
    return render(request, 'diretoria-vendedores.html', {'vendedores': vendedores})

@login_required(login_url='/')
def vendedor_criar_view(request: HttpRequest):
    if not request.user.is_superuser:
        return redirect('/vendedor/dashboard/')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if not username or not password:
            messages.error(request, 'Username e senha são obrigatórios.')
            return render(request, 'diretoria-vendedor-form.html', {'acao': 'criar'})
        if password != password2:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'diretoria-vendedor-form.html', {'acao': 'criar'})
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username já está em uso.')
            return render(request, 'diretoria-vendedor-form.html', {'acao': 'criar'})
        user = User.objects.create_user(
            username=username, email=email, password=password,
        )
        messages.success(request, f'Vendedor "{user.get_full_name() or user.username}" criado com sucesso.')
        return redirect('vendedores')
    return render(request, 'diretoria-vendedor-form.html', {'acao': 'criar'})

@login_required(login_url='/')
def vendedor_editar_view(request: HttpRequest, pk: int):
    if not request.user.is_superuser:
        return redirect('/vendedor/dashboard/')
    try:
        vendedor = User.objects.get(id=pk, is_superuser=False)
    except User.DoesNotExist:
        messages.error(request, 'Vendedor não encontrado.')
        return redirect('vendedores')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if not username:
            messages.error(request, 'Username é obrigatório.')
            return render(request, 'diretoria-vendedor-form.html', {'acao': 'editar', 'vendedor': vendedor})
        if password and password != password2:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'diretoria-vendedor-form.html', {'acao': 'editar', 'vendedor': vendedor})
        if User.objects.filter(username=username).exclude(id=pk).exists():
            messages.error(request, 'Username já está em uso.')
            return render(request, 'diretoria-vendedor-form.html', {'acao': 'editar', 'vendedor': vendedor})
        vendedor.username = username
        vendedor.email = email
        if password:
            vendedor.set_password(password)
        vendedor.save()
        messages.success(request, f'Vendedor "{vendedor.get_full_name() or vendedor.username}" atualizado com sucesso.')
        return redirect('vendedores')
    return render(request, 'diretoria-vendedor-form.html', {'acao': 'editar', 'vendedor': vendedor})

@login_required(login_url='/')
def vendedor_excluir_view(request: HttpRequest, pk: int):
    if not request.user.is_superuser:
        return redirect('/vendedor/dashboard/')
    if request.method == 'POST':
        try:
            user = User.objects.get(id=pk, is_superuser=False)
            user.delete()
            messages.success(request, 'Vendedor excluído com sucesso.')
        except User.DoesNotExist:
            messages.error(request, 'Vendedor não encontrado.')
        except Exception:
            messages.error(request, "Não foi possível excluir, pois existem vendas realizadas com este vendedor. ")
    return redirect('vendedores')

@login_required(login_url='/')
def produtos_view(request: HttpRequest):
    if not request.user.is_superuser:
        return redirect('/vendedor/dashboard/')

    produtos = Produto.objects.annotate(total_vendas=Count('vendas')).order_by('nome')

    for p in produtos:
        p.lucro = (p.preco_final or 0) - (p.custo_compra or 0)
        p.margem = ((p.lucro / p.preco_final) * 100) if p.preco_final else 0

    return render(request, 'diretoria-produtos.html', {'produtos': produtos})

@login_required(login_url='/')
def produto_criar_view(request: HttpRequest):
    if not request.user.is_superuser:
        return redirect('/vendedor/dashboard/')
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        custo_compra = request.POST.get('custo_compra', '').strip()
        preco_final = request.POST.get('preco_final', '').strip()
        quantidade_estoque = request.POST.get('quantidade_estoque', '0').strip()
        if not nome or not custo_compra or not preco_final:
            messages.error(request, 'Nome, custo e preço são obrigatórios.')
            return render(request, 'diretoria-produto-form.html', {'acao': 'criar'})
        try:
            custo_val = float(custo_compra.replace(',', '.'))
            preco_val = float(preco_final.replace(',', '.'))
            estoque_val = int(quantidade_estoque)
        except ValueError:
            messages.error(request, 'Valores numéricos inválidos.')
            return render(request, 'diretoria-produto-form.html', {'acao': 'criar'})
        if Produto.objects.filter(nome=nome).exists():
            messages.error(request, 'Já existe um produto com esse nome.')
            return render(request, 'diretoria-produto-form.html', {'acao': 'criar'})
        produto = Produto.objects.create(
            nome=nome, custo_compra=custo_val,
            preco_final=preco_val, quantidade_estoque=estoque_val,
        )
        messages.success(request, f'Produto "{produto.nome}" criado com sucesso.')
        return redirect('produtos')
    return render(request, 'diretoria-produto-form.html', {'acao': 'criar'})

@login_required(login_url='/')
def produto_editar_view(request: HttpRequest, pk: int):
    if not request.user.is_superuser:
        return redirect('/vendedor/dashboard/')
    try:
        produto = Produto.objects.get(id=pk)
    except Produto.DoesNotExist:
        messages.error(request, 'Produto não encontrado.')
        return redirect('produtos')
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        custo_compra = request.POST.get('custo_compra', '').strip()
        preco_final = request.POST.get('preco_final', '').strip()
        quantidade_estoque = request.POST.get('quantidade_estoque', '0').strip()
        if not nome or not custo_compra or not preco_final:
            messages.error(request, 'Nome, custo e preço são obrigatórios.')
            return render(request, 'diretoria-produto-form.html', {'acao': 'editar', 'produto': produto})
        try:
            custo_val = float(custo_compra.replace(',', '.'))
            preco_val = float(preco_final.replace(',', '.'))
            estoque_val = int(quantidade_estoque)
        except ValueError:
            messages.error(request, 'Valores numéricos inválidos.')
            return render(request, 'diretoria-produto-form.html', {'acao': 'editar', 'produto': produto})
        if Produto.objects.filter(nome=nome).exclude(id=pk).exists():
            messages.error(request, 'Já existe um produto com esse nome.')
            return render(request, 'diretoria-produto-form.html', {'acao': 'editar', 'produto': produto})
        produto.nome = nome
        produto.custo_compra = custo_val
        produto.preco_final = preco_val
        produto.quantidade_estoque = estoque_val
        produto.save()
        messages.success(request, f'Produto "{produto.nome}" atualizado com sucesso.')
        return redirect('produtos')
    return render(request, 'diretoria-produto-form.html', {'acao': 'editar', 'produto': produto})

@login_required(login_url='/')
def produto_excluir_view(request: HttpRequest, pk: int):
    if not request.user.is_superuser:
        return redirect('/vendedor/dashboard/')
    if request.method == 'POST':
        try:
            produto = Produto.objects.get(id=pk)
            nome = produto.nome
            produto.delete()
            messages.success(request, f'Produto "{nome}" excluído com sucesso.')
        except Produto.DoesNotExist:
            messages.error(request, 'Produto não encontrado.')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir, pois existem vendas realizadas com este produto.')
    return redirect('produtos')