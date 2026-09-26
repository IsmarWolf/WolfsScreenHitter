# WolfsScreenHitter

Aponta o cursor do mouse para um **alvo visual na tela**, encontrado em tempo real por cor ou por imagem de referência. O clique é sempre seu: o programa só posiciona o cursor, nunca clica.

Duas formas de reconhecer o alvo, ambas configuráveis por um arquivo JSON:

- **`shape`** — acha blobs de uma cor com formato próximo de um círculo. Serve para alvos coloridos, contornos, botões, indicadores.
- **`template`** — localize a imagem de uma letra, símbolo, ícone ou número usando correspondência de template em várias escalas. Serve para ler texto na tela.

Roda em Windows, com o alvo em qualquer área que você escolher: janela específica, área central dessa janela, tela inteira, monitor virtual ou um retângulo fixo.

## Testes

Dois scripts, sem framework extra. Nenhum dos dois mexe no seu mouse por padrão: as partes que movem o cursor são opt-in.

O primeiro é seguro para rodar a qualquer momento:

```bash
python tests/test_local.py
```

Verifica de forma offline que não existe nenhuma chamada de clique no pacote, que `pyautogui` não é dependência, que os perfis carregam e que detectores, regiões e modos de movimento se comportam. Termina sozinho, com uma linha por verificação.

O segundo mexe no seu mouse e foca uma janela por alguns segundos, então ele não faz nada sem a flag:

```bash
python tests/test_e2e.py --executar
```

Faz o teste de verdade: cria uma cena com um anel claro e um anel vermelho, abre no visualizador do Windows, captura a tela real por DXGI, confirma que detectou o anel claro e ignorou o vermelho, e move o cursor para o centro do alvo.

As duas verificações de movimento do `test_local.py` também são opt-in:

```bash
python tests/test_local.py --executar
```

Sem a flag elas aparecem como `[pulado]`, e o resto continua sendo verificado. Use `--executar` quando não estiver digitando, porque o cursor vai saltar pela tela.

## O que o programa não faz

- Não clica. Não existe nenhuma chamada de botão no código, e há um teste que garante isso.
- Não digita nada.
- Não envia eventos de rede nem lê nada fora da área que você definiu.

Se você precisa de clique automático, este não é o projeto certo.

## Instalação

Requer Python 3.10 ou superior.

```bash
git clone https://github.com/IsmarWolf/WolfsScreenHitter.git
cd WolfsScreenHitter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Opcionalmente, para ter o comando `wolfs-screen-hitter` disponível:

```bash
pip install -e .
```

## Uso rápido

```bash
# ver o que existe
python -m wolfs_screen_hitter list-profiles
python -m wolfs_screen_hitter list-windows

# testar a detecção sem mexer no mouse (sempre comece aqui)
python -m wolfs_screen_hitter check profiles/circulo_claro.json --debug out/debug.png

# seguir o alvo de verdade
python -m wolfs_screen_hitter run profiles/circulo_claro.json
```

Pare com **Esc**, **F12**, ou deixando o mouse parado no canto superior esquerdo por um segundo.

O comando `check` é o mais útil para ajustar um perfil: ele diz se achou, onde está, e salva uma imagem com a caixa destacada para você ver o que o detector enxergou.

## Funciona em qualquer tela

O programa não sabe, e não precisa saber, qual programa é o seu alvo. Ele não procura por nome de jogo, nem por janela específica, a menos que você peça. Por padrão o perfil `circulo_claro.json` varre a tela inteira e reconhece o alvo pelo formato e pela cor.

Isso significa que a mesma configuração serve para um jogo, um vídeo, um gráfico, uma planilha, um PDF ou qualquer outra coisa que desenhe um alvo na tela. O que o detector enxerga são pixels, não aplicativos.

### Escolhendo onde procurar

Tudo é o bloco `region`. Quatro opções, e elas se trocam sem mudar mais nada:

| `mode` | Onde olha | Quando usar |
|---|---|---|
| `screen` | A tela primária inteira | Padrão. Serve para a maioria dos casos. |
| `virtual` | Todos os monitores ao mesmo tempo | Alvo em outro monitor, ou mais de um monitor. |
| `window` | Só a janela de `window.title` | Muita coisa na tela se parece com o alvo. |
| `fixed` | Um retângulo que você escolhe | Você sabe exatamente onde o alvo aparece. |

Para usar em **qualquer monitor**, troque para o desktop inteiro:

```json
"region": { "mode": "virtual" }
```

Para usar **só numa janela**, aponte pelo título e descarte as bordas com a margem:

```json
"window": { "title": "MeuPrograma" },
"region": { "mode": "window", "margin": 130 }
```

Para fixar **um lugar exato**, use coordenadas:

```json
"region": { "mode": "fixed", "left": 640, "top": 300, "width": 640, "height": 480 }
```

### A diferença que importa: janela ou tela toda

Escolher `screen` é o mais fácil e o mais abrangente, mas tem uma consequência: o detector vê **tudo que estiver visível**, incluindo a interface dos seus próprios programas. Se você tem um ícone claro e redondo no canto da tela, ele é um candidato tão válido quanto o alvo de verdade, e o detector vai escolher o maior.

Quando isso acontecer, estreite a busca. O `margin` é a ferramenta certa: ela apaga uma faixa em volta da janela, jogando fora ícones, botões e barras de status que ficam nas bordas.

Como descobrir a margem certa para o seu caso: comece em `0`, rode o `check` com `--debug`, e olhe onde a caixa verde caiu. Se caiu em um ícone da borda, aumente a margem até o suficiente para cortar aquele ícone. Se a caixa someu junto com o alvo, diminua.

Para descobrir o título exato da janela, rode `list-windows` e copie o nome que aparece.

### Um detalhe sobre o que está visível

O detector trabalha no que a câmera de tela enxerga, ou seja, o que está **desenhado na tela**. Se outra janela estiver por cima do alvo, o alvo não existe para o detector. Isso não é defeito: é o que qualquer captura de tela faz.

Se você usa o modo `tela` e o alvo some do nada, geralmente é porque o seu navegador, terminal ou editor passou para a frente. Nesse caso, `window` é o modo certo.

## Como ajustar um perfil para o seu alvo

O fluxo sempre é o mesmo: copia um perfil de exemplo, ajusta o `target`, testa com `check` olhando o `--debug`, repete. Você nunca precisa mexer em Python.

### Se o alvo é claro e redondo

Copie `profiles/circulo_claro.json`. Esse é o caso mais comum e já vem pronto.

### Se o alvo é escuro

Troque `bright` por `dark`. O `v_max` é o brilho máximo, então um alvo preto sobre fundo claro usa algo entre `40` e `90`:

```json
"target": {
  "dark": { "v_max": 80, "s_max": 120 },
  "size": { "min": 45, "max": 240 },
  "aspect": { "min": 0.65, "max": 1.5 },
  "fill": { "min": 0.04, "max": 0.4 }
}
```

### Se o alvo tem uma cor viva

Cores fortes são descartadas por `bright` e por `dark` porque têm saturação alta. Use uma faixa HSV. Os valores são `[matiz, saturação, valor]`, e o matiz vai de 0 a 179 no OpenCV:

| Cor | `hsv_min` | `hsv_max` |
|---|---|---|
| Vermelho | `[0, 140, 140]` | `[10, 255, 255]` |
| Laranja/amarelo | `[11, 140, 140]` | `[30, 255, 255]` |
| Verde | `[35, 90, 90]` | `[85, 255, 255]` |
| Azul | `[100, 90, 90]` | `[130, 255, 255]` |
| Roxo | `[130, 90, 90]` | `[160, 255, 255]` |
| Rosa | `[160, 90, 140]` | `[179, 255, 255]` |

Copie `profiles/faixa_hsv.json`, que já usa vermelho, e troque os dois trios.

Para descobrir o matiz de um pixel, use a captura que o próprio programa gravou:

```bash
python -m wolfs_screen_hitter capture captura.png
python -m wolfs_screen_hitter crop captura.png matiz.png 640 300 1 1
```

Um `1x1` de um ponto do alvo. Depois leia o tri HSV com o Python:

```bash
python -c "import cv2; print(cv2.cvtColor(cv2.imread('matiz.png', cv2.IMREAD_COLOR), cv2.COLOR_BGR2HSV)[0][0])"
```

### Se o alvo não é redondo

Ajuste `aspect` e espere que o `fill` aceite a forma. Um losango ou um triângulo costuma passar com `aspect` entre `0.5` e `2.0` e `fill` de `0.2` a `0.6`. Se for um retângulo cheio, suba o teto do `fill` para `1.0`.

### Se o alvo é uma letra, número ou ícone

Use o detector `template` em vez do `shape`. O passo a passo completo está em [Como detectar uma letra ou símbolo](#como-detectar-uma-letra-ou-símbolo).

## Receitas para os problemas comuns

Estes são os ajustes que resolvem quase tudo. Sempre comece testando com `check --debug` antes de mudar qualquer número.

**Não acha nada, e eu sei que o alvo está na tela**

Quase sempre é o `work_scale` removendo o alvo. Se o alvo tem menos de uns 40 px, baixe para `0.35` ou coloque `1.0`. Se o alvo é pequeno por natureza, baixe também o `size.min`.

**Acha, mas a caixa cai no lugar errado**

Baixe o teto do `fill` para descartar blocos sólidos, ou suba `aspect` para descartar barras e faixas. Se o alvo verdadeiro é menor que o falso positivo, o detector escolhe o maior por padrão, então aperte o `size.max`.

**Acha um ícone ou botão da interface**

Não mexa no `target`, mexa no `region`. Use `mode: "window"` com `margin`, ou `mode: "fixed"` limitando a área.

**Acha o alvo mas o cursor não vai até ele**

Isso é o programa de destino ignorando movimento instantâneo. Troque `"mode": "teleport"` por `"mode": "smooth"`.

**O alvo pisca e o programa parece perder ele**

Normal. O laço só age quando há detecção. Se quiser suavizar, reduza o `work_scale` para `0.35`: imagem menor significa menos ruído e mais chance de acertar em quadros intermediários.

**A janela do alvo tem bordas ou barras que atrapalham**

Use `margin`. Comece em `0` e aumente aos poucos, conferindo no `--debug` a cada passo.

**Está lento em monitor grande**

Baixe o `work_scale` para `0.35`, ou troque `screen` por `window` com margem, que captura bem menos pixels.

**Quero o cursor mais rápido ou mais lento no `smooth`**

`duration` é o tempo total do movimento, em segundos. `0.08` é rápido, `0.30` é devagar e discreto. `jitter` é o tremor, em pixels.

## Como funciona

```
wolfs_screen_hitter/
  win.py        acessos ao Win32: cursor, teclas, envio de movimento
  capture.py    captura de tela (DXGI, com queda para mss)
  windows.py    enumeração de janelas e resolução da região de busca
  detect.py     os dois detectores: forma por cor e template
  profiles.py   leitura e validação dos perfis JSON
  pointer.py    modos de movimento do cursor
  app.py        loop principal e comandos de linha
```

O ciclo é: capturar a região → detectar → mover o cursor → repetir. A captura DXGI leva cerca de 2 ms e a detecção alguns milissegundos, o que dá mais de cem quadros por segundo na captura de tela inteira.

## Perfis

Um perfil é um JSON que descreve **o que procurar, onde procurar e como reagir**.

### O perfil mínimo

Na maioria dos casos, tudo que você precisa é isto:

```json
{
  "detector": "shape",
  "region": { "mode": "screen" },
  "target": {
    "bright": { "v_min": 150, "s_max": 110 },
    "size": { "min": 45, "max": 240 },
    "fill": { "min": 0.04, "max": 0.4 }
  }
}
```

Sem `window`, sem nome de programa: o detector varre a tela e acha qualquer alvo claro e redondo que esteja visível. É o perfil mais genérico possível, e é o que resolve a maioria dos casos.

### Estrutura completa

Todos os campos, com os valores padrão que valem quando você omite:

```json
{
  "name": "Meu alvo",
  "detector": "shape",

  "window": {
    "title": "MeuPrograma",
    "min_width": 200,
    "min_height": 200
  },

  "region": {
    "mode": "window",
    "margin": 0
  },

  "target": {
    "bright": { "v_min": 150, "s_max": 110 },
    "size":   { "min": 45, "max": 240 },
    "aspect": { "min": 0.65, "max": 1.5 },
    "fill":   { "min": 0.04, "max": 0.4 },
    "work_scale": 0.5
  },

  "pointer": { "mode": "teleport" },
  "controls": { "corner_seconds": 1.0 }
}
```

### `region` — onde procurar

| `mode` | Significado |
|---|---|
| `window` | Área da janela de `window.title`. Use `margin` para descartar as bordas. |
| `screen` | Tela primária inteira. |
| `virtual` | Todos os monitores juntos. |
| `fixed` | Retângulo fixo, com `left`, `top`, `width`, `height`. |

O `margin` é o truque mais útil: muitos programas desenham ícones perto das bordas, e `margin: 130` tira eles da consideração.

### `target` — o que é o alvo

Dois jeitos de descrever a cor:

```json
"bright": { "v_min": 150, "s_max": 110 }
```

acha pixels claros e pouco saturados. `v_min` é o brilho mínimo, `s_max` é a saturação máxima. Um `s_max` baixo exclui vermelho e verde fortes, então essa combinação acha branco, cinza e bege sem pegar cor viva.

```json
"dark": { "v_max": 80, "s_max": 120 }
```

acha pixels escuros. Dá para usar `bright` e `dark` juntos: o alvo passa a ser a união dos dois.

```json
"hsv_min": [0, 140, 140],
"hsv_max": [12, 255, 255]
```

escolhe uma faixa exata de matiz, saturação e valor. `hsv_min` e `hsv_max` substituem `bright`/`dark` quando presentes. Útil para uma cor específica, por exemplo vermelho vivo: matiz de 0 a 12.

Os filtros de forma:

| Campo | O que restringe |
|---|---|
| `size` | Lado do alvo em pixels, de `min` a `max`. |
| `aspect` | Razão entre largura e altura. `1.0` é um quadrado, `0.5` é duas vezes mais largo que alto. |
| `fill` | Fração da caixa preenchida por pixels do alvo. Um contorno fino fica perto de `0.1`; um bloco sólido fica perto de `1.0`. É o filtro que separa um anel de um retângulo. |
| `area_min` | Área mínima em pixels, para descartar ruído. |
| `work_scale` | Redução da imagem antes de procurar. `0.5` acelera bastante e ainda acha alvos de 40 px ou mais. |

Quando mais de um candidato passa nos filtros, vence o **maior**.

### `pointer` — como o cursor se move

| `mode` | Comportamento |
|---|---|
| `teleport` | Vai direto para o centro. É o padrão, e o mais rápido. |
| `smooth` | Percorre um caminho curvo, com tremor e passos irregulares, como uma mão. Use quando o programa de destino ignorar movimento instantâneo. |

Para `smooth` você pode ajustar `duration` (em segundos) e `jitter` (amplitude do tremor, em pixels).

## Como detectar uma letra ou símbolo

O detector `template` funciona com uma imagem de referência. O fluxo completo:

**1. Tire uma captura da tela com o alvo visível**

```bash
python -m wolfs_screen_hitter capture captura.png
```

**2. Recorte só a letra ou símbolo**

Use as coordenadas da captura. O comando já mostra o tamanho da imagem:

```bash
python -m wolfs_screen_hitter crop captura.png profiles/templates/alvo.png 640 300 48 52
```

Isso salva um recorte `48x52` daquele ponto. Guarde o original, porque ele é a captura de tela, e o recorte é o template.

**3. Aponte um perfil para o template**

```json
{
  "name": "Letra alvo",
  "detector": "template",
  "window": { "title": null },
  "region": { "mode": "window", "margin": 0 },
  "target": {
    "template": "templates/alvo.png",
    "threshold": 0.8,
    "scale_min": 0.5,
    "scale_max": 2.0,
    "scale_steps": 12,
    "work_scale": 1.0,
    "invert": false
  },
  "pointer": { "mode": "teleport" }
}
```

O caminho do template é relativo ao arquivo do perfil, então dá para manter os templates em `profiles/templates/`.

**4. Teste antes de usar**

```bash
python -m wolfs_screen_hitter check profiles/letra_template.json --debug out/debug.png
```

### Ajustando o template

| Campo | Efeito |
|---|---|
| `threshold` | Semelhança mínima para aceitar, de 0 a 1. Comece em `0.8`. Baixe para `0.7` se não achar. Suba para `0.9` se estiver pegando o lugar errado. |
| `scale_min` / `scale_max` | Faixa de tamanhos a testar. Se o alvo na tela é maior ou menor que o recorte, amplie a faixa. |
| `scale_steps` | Quantos tamanhos são testados dentro da faixa. Mais passos, mais chance e mais custo. |
| `work_scale` | Redução para acelerar. Com `0.5`, a tolerância a ruído cai. |
| `invert` | Inverte a escala de cinza dos dois lados. Use quando o alvo for escuro sobre fundo claro e o `threshold` não passar. |

### Dicas para templates que não funcionam

- **Corte justo.** Sobras de fundo no template pioram a correspondência. Encoste nas bordas do glifo.
- **Fundo parecido com o da tela.** Se o template tem fundo branco e a tela é escura, use `invert: true` ou tire o fundo do recorte.
- **Escala conta.** Se o alvo na tela tem o dobro do tamanho do recorte, ponha `scale_min: 1.5`.
- **Palavras não são um alvo só.** Faça um template por letra, ou por símbolo, e um perfil para cada. O detector devolve sempre a melhor correspondência da imagem que você deu.
- **Vários alvos iguias na tela.** O detector devolve sempre a maior pontuação. Se você precisa de um alvo específico, recorte a região em `region.fixed` para fechar o resto da tela.

## Quando o `shape` é melhor que o `template`

Use `shape` quando o alvo é uma **cor** e o formato não importa muito. É mais rápido e mais estável, porque não depende de template exato nem de escala.

Use `template` quando o que identifica o alvo é a **forma ou o texto**, e a cor pode variar.

## Solução de problemas

**`check` diz que não achou nada**

Grave o debug e veja o que o detector enxerga:

```bash
python -m wolfs_screen_hitter check profiles/meu.json --debug out/debug.png
```

Se a caixa verde não aparece, o alvo não passou nos filtros. Alimente `size`, afrouxe `aspect`, aumente `fill` e cheque se `bright`/`dark` descrevem bem a cor.

**Achei o lugar errado**

Geralmente é um elemento de interface parecido. Restrinja a região com `region.margin`, ou reduza `fill` se o alvo verdadeiro é mais fino que o falso positivo.

**O cursor não se move**

Confira a saída de `list-windows` e o `title` no perfil. Títulos só precisam bater parcialmente: `"title": "Paint"` acha `"Paint - imagem.png"`.

**O alvo aparece em varios lugares**

`template` devolve sempre a melhor pontuação. Feche a área de busca com `region.fixed` para isolar.

**Está lento**

Aumente `work_scale` para `0.35` no perfil `shape`, ou reduza `scale_steps` no `template`. A captura DXGI é rápida; o custo está na detecção.

**O programa alvo ignora o movimento do cursor**

Troque `"mode": "teleport"` por `"mode": "smooth"`. Alguns programas registram apenas eventos de movimento encadeados.

## Privacidade

Tudo roda local. Nenhuma informação sai da máquina, e a captura fica restrita à região que você configurou no perfil.

## Licença

MIT. Veja [LICENSE](LICENSE).
