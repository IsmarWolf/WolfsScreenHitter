# WolfsScreenHitter

[English](README.md) | [Português](README.pt.md)

Aponta o cursor do mouse para um **alvo visual na tela**, encontrado em tempo real por cor ou por imagem de referência. O clique é sempre seu: o programa só posiciona o cursor, nunca clica.

Duas formas de reconhecer o alvo, ambas configuradas por um arquivo JSON:

- **`shape`** — acha blobs de uma cor com formato próximo de um círculo. Serve para alvos coloridos, contornos, botões, indicadores.
- **`template`** — localiza a imagem de uma letra, símbolo, ícone ou número usando correspondência de template em várias escalas. Serve para ler texto na tela.

Roda em Windows, com o alvo em qualquer área que você escolher: janela específica, área central dessa janela, tela inteira, desktop virtual ou um retângulo fixo.

---

## Instalação

### 1. Requisitos

- Windows 10 ou 11
- Python 3.10 ou superior (`python --version`)

### 2. Instalar

```bash
git clone https://github.com/IsmarWolf/WolfsScreenHitter.git
cd WolfsScreenHitter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

As únicas dependências são `opencv-python`, `numpy`, `dxcam` e `mss`. Nada além disso, e não precisa de GPU.

Opcionalmente instale o pacote em si, o que dá o comando `wolfs-screen-hitter`:

```bash
pip install -e .
```

### 3. Primeira execução

Comece aqui, antes de qualquer outra coisa. Isto checa a detecção uma vez e não mexe em nada:

```bash
python -m wolfs_screen_hitter check profiles/circulo_claro.json --debug out/debug.png
```

Abra `out/debug.png`. Uma caixa verde no seu alvo significa que a instalação funciona. Sem caixa, o alvo ainda não corresponde ao perfil — vá para [Solução de problemas](#solução-de-problemas).

Duas coisas sobre o que você acabou de rodar:

- O perfil de exemplo usa `region: "screen"`, então ele olha a tela primária inteira e espera ver um alvo claro e redondo em algum lugar dela. Se você não tiver um na tela agora, ele reporta que não achou nada, e isso está certo. Não é instalação quebrada.
- O detector só enxerga o que está **desenhado na tela**. Se o alvo estiver coberto por outra janela, para o detector ele não existe.

### 4. Rodar de verdade

```bash
python -m wolfs_screen_hitter run profiles/circulo_claro.json
```

Pare com **Esc**, **F12**, ou deixando o mouse parado no canto superior esquerdo por um segundo.

### 5. Deixar com a sua cara

Copie um dos perfis de exemplo e edite o bloco `target`. Os perfis que acompanham o projeto:

| Perfil | Para quê |
|---|---|
| `profiles/circulo_claro.json` | Alvo claro e redondo, em qualquer tela. Comece por este. |
| `profiles/faixa_hsv.json` | Alvo de uma cor viva específica, por faixa HSV. |
| `profiles/letra_template.json` | Letra, número ou ícone, por imagem de template. |

O ciclo é sempre o mesmo: copie um perfil, ajuste o `target`, teste com `check --debug`, repita. Você nunca precisa mexer em Python. As receitas estão em [Ajustando um perfil](#ajustando-um-perfil).

**Ou edite numa janela**

```bash
python -m wolfs_screen_hitter.gui
```

O mesmo perfil, numa janela. **Novo** pede um nome e grava o arquivo na hora, então todo perfil do dropdown já tem nome. A janela tem duas abas: **Configurações**, com o que se responde sem pensar, e **Ajustes finos**, com os números. Você troca de aba o tempo todo e nada se perde: as duas gravam no mesmo perfil. Os grupos de campos abrem um de cada vez, e os campos que exigiriam abrir um JSON para entender ganharam um botão no lugar:

- **Selecionar na tela** cobre a tela principal. Arraste um retângulo em volta do alvo e os quatro números da região se preenchem. **Esc** cancela.
- O campo do template tem um botão de pasta ao lado, para você escolher o PNG em vez de digitar um caminho.

Na aba **Configurações** ficam o nome do perfil, o título da janela, a região, o detector, o arquivo do template e o tipo de movimento do cursor. Na de **Ajustes finos** ficam o brilho, a saturação, o tamanho, a proporção, o preenchimento, a área, o limiar, a faixa HSV, a escala de trabalho, a margem, o tamanho mínimo da janela, a duração e o tremor do cursor, e os segundos no canto. Os padrões já funcionam na maioria dos casos: se você não sabe o que é "preenchimento máximo", não precisa mexer nele.

Um perfil criado aqui é um JSON comum na pasta `profiles/`. A janela e a linha de comando leem a mesma coisa.

---

## Comandos

| Comando | O que faz |
|---|---|
| `check PERFIL` | Procura uma vez, reporta, opcionalmente desenha uma imagem de debug. Não move nada. |
| `run PERFIL` | Segue o alvo em laço e posiciona o cursor. |
| `capture ARQUIVO` | Salva a captura da janela que estava em foco, ou da tela inteira se não houver janela para pegar. |
| `crop ORIGEM DESTINO X Y L A` | Recorta um template de uma captura. |
| `list-profiles` | Mostra os perfis disponíveis. |
| `list-windows` | Lista as janelas visíveis com tamanho e posição. |

Cada flag pertence a um comando só, e o argparse avisa se você misturar:

| Flag | No comando | O que faz |
|---|---|---|
| `--debug ARQUIVO` | `check` | Salva o que o detector viu, com o alvo marcado. |
| `--tentativas N` | `check` | Repete a detecção até `N` vezes, `40` por padrão. |
| `--espera S` | `check` | Pausa entre essas repetições, `0.05` segundos por padrão. |
| `--interval S` | `run` | Pausa entre quadros do laço, `0.002` segundos por padrão. |
| `--dry-run` | `run` | Roda a mesma detecção do `check` e nunca move o mouse. |
| `--delay S` | `capture` | Espera `S` segundos antes de capturar, para um menu que você vai abrir. |

Duas coisas que o `run --dry-run` não faz: não aceita `--debug`, e sempre usa o `--tentativas` e o `--espera` padrão. Use o `check` quando quiser imagem de debug ou mais retentativas.


---

## Como funciona

```
wolfs_screen_hitter/
  win.py        acessos ao Win32: cursor, teclas, envio de movimento
  capture.py    captura de tela (DXGI, com queda para mss)
  windows.py    enumeração de janelas e resolução da região de busca
  detect.py     os dois detectores: forma por cor e template
  profiles.py   leitura e validação dos perfis JSON
  pointer.py    modos de movimento do cursor
  app.py        laço principal e comandos de linha
```

O ciclo é: capturar a região → detectar → mover o cursor → repetir. A captura DXGI leva cerca de 2 ms e a detecção alguns milissegundos, o que dá mais de cem quadros por segundo na captura de tela inteira.

A captura passa por DXGI primeiro e cai para `mss` sozinha se o DXGI não estiver disponível, como acontece em alguns notebooks com GPU híbrida.

---

## Funciona em qualquer tela

O programa não sabe, e não precisa saber, qual programa é o seu alvo. Ele não procura por nome de jogo, nem por janela específica, a menos que você peça.

Isso significa que a mesma configuração serve para um jogo, um vídeo, um gráfico, uma planilha, um PDF ou qualquer outra coisa que desenhe um alvo na tela. O que o detector enxerga são pixels, não aplicativos.

### Escolhendo onde procurar

Tudo é o bloco `region`. Quatro opções, e você troca entre elas sem mudar mais nada:

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
"window": { "title": "MyProgram" },
"region": { "mode": "window", "margin": 130 }
```

Para fixar **um lugar exato**, use coordenadas:

```json
"region": { "mode": "fixed", "left": 640, "top": 300, "width": 640, "height": 480 }
```

### Tela toda ou janela?

Escolher `screen` é o mais fácil e o mais abrangente, mas tem uma consequência: o detector vê **tudo que estiver visível**, incluindo a interface dos seus próprios programas. Se você tem um ícone claro e redondo no canto da tela, ele é um candidato tão válido quanto o alvo de verdade, e o detector vai escolher o maior.

Quando isso acontecer, estreite a busca. O `margin` é a ferramenta certa: ela apaga uma faixa em volta da janela, jogando fora os ícones, botões e barras de status que ficam perto das bordas.

Para descobrir a margem certa do seu caso: comece em `0`, rode o `check` com `--debug` e olhe onde a caixa verde caiu. Se caiu em um ícone da borda, aumente a margem até cortar aquele ícone. Se a caixa sumiu junto com o alvo, diminua.

Para descobrir o título exato da janela, rode `list-windows` e copie o nome que aparece. Títulos só precisam bater parcialmente, então `"title": "Paint"` acha `"Paint - imagem.png"`.

---

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

Todos os campos, com o valor padrão que vale quando você omite:

```json
{
  "name": "Meu alvo",
  "detector": "shape",

  "window": {
    "title": "MyProgram",
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

| Chave | Significado |
|---|---|
| `mode` | `window`, `screen`, `virtual` ou `fixed`, como descrito acima. |
| `margin` | Pixels descartados de cada borda. Só usado no modo `window`. |
| `left`, `top`, `width`, `height` | O retângulo, só usado no modo `fixed`. |

### `target` — o que é o alvo

Dois jeitos de descrever a cor:

```json
"bright": { "v_min": 150, "s_max": 110 }
```

acha pixels claros e pouco saturados. `v_min` é o brilho mínimo, `s_max` a saturação máxima. Um `s_max` baixo exclui vermelho e verde fortes, então essa combinação acha branco, cinza e bege sem pegar cor viva.

```json
"dark": { "v_max": 80, "s_max": 120 }
```

acha pixels escuros. Dá para usar `bright` e `dark` juntos: o alvo passa a ser a união dos dois.

```json
"hsv_min": [0, 140, 140],
"hsv_max": [12, 255, 255]
```

escolhe uma faixa exata de matiz, saturação e valor. `hsv_min` e `hsv_max` substituem `bright`/`dark` quando presentes. Os valores são `[matiz, saturação, valor]`, e o matiz vai de 0 a 179 no OpenCV:

| Cor | `hsv_min` | `hsv_max` |
|---|---|---|
| Vermelho | `[0, 140, 140]` | `[10, 255, 255]` |
| Laranja/amarelo | `[11, 140, 140]` | `[30, 255, 255]` |
| Verde | `[35, 90, 90]` | `[85, 255, 255]` |
| Azul | `[100, 90, 90]` | `[130, 255, 255]` |
| Roxo | `[130, 90, 90]` | `[160, 255, 255]` |
| Rosa | `[160, 90, 140]` | `[179, 255, 255]` |

Os filtros de forma:

| Campo | O que restringe |
|---|---|
| `size` | Lado do alvo em pixels, de `min` a `max`. |
| `aspect` | Razão entre largura e altura. `1.0` é um quadrado, `0.5` é duas vezes mais largo que alto. |
| `fill` | Fração da caixa preenchida por pixels do alvo. Um contorno fino fica perto de `0.1`; um bloco sólido fica perto de `1.0`. É o filtro que separa um anel de um retângulo. |
| `area_min` | Área mínima em pixels, para descartar ruído. |
| `work_scale` | Redução da imagem antes de procurar. `0.5` acelera bastante e ainda acha alvos de 40 px ou mais. |

Quando mais de um candidato passa nos filtros, vence o **maior**.

### Ajustando um perfil

O fluxo é sempre o mesmo: copie um perfil de exemplo, ajuste o `target`, teste com `check` olhando a imagem de `--debug`, repita. Você nunca precisa mexer em Python.

Salve o arquivo em UTF-8. A marca de ordem de byte não atrapalha, então um perfil escrito pelo `Set-Content -Encoding UTF8` do PowerShell 5.1 carrega sem reclamar.

**Alvo claro e redondo.** Copie `profiles/circulo_claro.json`. É o caso mais comum e já vem pronto.

**Alvo escuro.** Troque `bright` por `dark`. O `v_max` é o brilho máximo, então um alvo preto sobre fundo claro usa algo entre `40` e `90`:

```json
"target": {
  "dark": { "v_max": 80, "s_max": 120 },
  "size": { "min": 45, "max": 240 },
  "aspect": { "min": 0.65, "max": 1.5 },
  "fill": { "min": 0.04, "max": 0.4 }
}
```

**Cor viva.** Pixel saturado não é `bright` nem `dark` a não ser que o perfil limite o `s_max`, e o padrão do código, `255`, não limita nada. Use uma faixa HSV da tabela acima. Copie `profiles/faixa_hsv.json`, que já usa vermelho, e troque os dois trios. Esse perfil também vem com `region.mode` em `fixed` num retângulo de `1920x1080`, então troque para `screen` a não ser que você queira mesmo um retângulo fixo.

**Não redondo.** Ajuste `aspect` e espere que o `fill` aceite a forma. Um losango ou um triângulo costuma passar com `aspect` entre `0.5` e `2.0` e `fill` de `0.2` a `0.6`. Se for um retângulo cheio, suba o teto do `fill` para `1.0`.

**Letra, número ou ícone.** Use o detector `template` em vez do `shape`. Veja [Detectar uma letra ou símbolo](#detectar-uma-letra-ou-símbolo).

### `pointer` — como o cursor se move

| `mode` | Comportamento |
|---|---|
| `teleport` | Vai direto para o centro. Padrão, e o mais rápido. |
| `smooth` | Percorre um caminho curvo, com tremor e passos irregulares, como uma mão. Use quando o programa de destino ignorar movimento instantâneo. |

Para `smooth` você pode ajustar `duration` (tempo total do movimento, em segundos) e `jitter` (amplitude do tremor, em pixels). `0.08` é rápido, `0.30` é devagar e discreto.

### `controls` — quando parar

| Campo | Significado |
|---|---|
| `corner_seconds` | Quanto tempo o mouse precisa ficar no canto superior esquerdo para parar. Padrão `1.0`. |

**Esc** e **F12** sempre param o laço, independente deste campo.

### Quando o `shape` vence o `template`

Use `shape` quando o alvo é uma **cor** e o formato não importa muito. É mais rápido e mais estável, porque não depende de template exato nem de escala.

Use `template` quando o que identifica o alvo é a **forma ou o texto**, e a cor pode variar.

---

## Detectar uma letra ou símbolo

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
  "name": "Minha letra",
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
| `threshold` | Semelhança mínima para aceitar, de 0 a 1. Comece em `0.8`. Baixe para `0.7` se não acha. Suba para `0.9` se está pegando o lugar errado. |
| `scale_min` / `scale_max` | Faixa de tamanhos a testar. Se o alvo na tela é maior ou menor que o recorte, amplie a faixa. |
| `scale_steps` | Quantos tamanhos são testados dentro da faixa. Mais passos, mais chance e mais custo. |
| `work_scale` | Redução para acelerar. Com `0.5`, a tolerância a ruído cai. |
| `invert` | Inverte a escala de cinza dos dois lados. Use quando o alvo for escuro sobre fundo claro e o `threshold` não passar. |

### Lendo a cor do seu alvo

Quando você não sabe que cor colocar no perfil, deixe a ferramenta medir. Tire uma captura, recorte um pixel `1x1` do meio do alvo e leia o valor:

```bash
python -m wolfs_screen_hitter capture captura.png
python -m wolfs_screen_hitter crop captura.png matiz.png 640 300 1 1
python -c "import cv2; print(cv2.cvtColor(cv2.imread('matiz.png', cv2.IMREAD_COLOR), cv2.COLOR_BGR2HSV)[0][0])"
```

A saída é o trio `[matiz, saturação, valor]`. Use direto como `hsv_min`, e como `hsv_max` com os canais aumentados.

---

## Solução de problemas

Tudo que costuma dar errado, em uma tabela só. Ache seu sintoma, leia a causa, aplique a correção.

### Detecção

| Sintoma | Causa | Correção |
|---|---|---|
| Não acha nada, e o alvo está ali na tela | O `work_scale` encolheu o alvo para baixo do `size.min` | Suba para perto de `1.0`. Um `work_scale` baixo é para velocidade, não para alvo pequeno |
| Não acha nada | Alvo menor que o `size.min` | Baixe o `size.min` |
| Não acha nada | `bright`/`dark` não descrevem a cor | [Leia o valor real](#lendo-a-cor-do-seu-alvo) e use |
| Não acha nada, e o alvo é cor viva | O perfil limita a saturação com `s_max`, então pixel saturado não é `bright` nem `dark` | Use `hsv_min`/`hsv_max`. O padrão do código é `s_max` `255`, que aceita qualquer saturação |
| Não acha nada, e o alvo é pequeno ou fino | Filtros de tamanho e preenchimento apertados | Alargue o `size`, afrouxe o `aspect`, baixe o piso do `fill` |
| A caixa cai num ícone ou botão da interface | O modo tela também vê a sua própria interface | Use `region: "window"` com `margin`, ou `region: "fixed"` |
| A caixa cai na forma parecida errada | Filtros largos demais | Baixe o teto do `fill`, aperte o `aspect` |
| Pega o falso positivo maior | No `shape` sempre vence o maior bloco | Baixe o `size.max` para menos que o alvo verdadeiro |
| O alvo pisca e o programa parece perder ele | A detecção roda nos quadros crus | Baixe o `work_scale` para `0.35` |
| O alvo parece retângulo, não círculo | `aspect` apertado demais | Alargue o `aspect`, e suba o teto do `fill` para `1.0` se for bloco cheio |

### Localização

| Sintoma | Causa | Correção |
|---|---|---|
| O alvo some do nada | Outra janela está por cima | Traga para a frente, ou use `region: "window"` |
| O alvo aparece em vários lugares | Só volta um resultado: o `shape` fica com o maior bloco, o `template` fica com a melhor correspondência | Feche a área com `region: "fixed"` |
| Bordas e barras da janela atrapalham | A busca inclui a moldura | Use `margin`, comece em `0` e aumente olhando o `--debug` |
| Está procurando a janela errada | O `title` não bate | Rode `list-windows`. A comparação ignora maiúsculas e é parcial, então um trecho distintoivo basta |
| Fica imprimindo `Aguardando a janela...` | A janela é menor que `window.min_width`/`min_height`, que valem `200` por padrão | Baixe os dois no perfil, ou abra a janela maior |
| A região saiu vazia | Nenhuma janela casou, ou o retângulo degenerou | Rode `check` para ver a região resolvida e ajuste `window.title` ou `region` |
| O alvo está no segundo monitor | `screen` só cobre a primária | Use `region: "virtual"` |

### Movimento

| Sintoma | Causa | Correção |
|---|---|---|
| O cursor não se move | Nada foi detectado | Rode `check` primeiro; se não achar, resolva a detecção |
| Eu movo o mouse e ele volta para o alvo | O laço recentraliza o cursor a cada quadro, de propósito | Pare com **Esc** ou **F12**. Nenhuma configuração de `pointer` devolve o controle; `smooth` só muda o caminho |
| Cursor rápido ou lento demais no `smooth` | `duration` e `jitter` | `duration` `0.08` rápido, `0.30` devagar; `jitter` é o tremor em pixels |
| Não consegue parar o laço | Não são as teclas usuais | **Esc** ou **F12**; ou deixe o mouse no canto superior esquerdo por `corner_seconds` |

### Templates

| Sintoma | Causa | Correção |
|---|---|---|
| O template nunca casa | O `threshold` é `0.80` por padrão e a correspondência fica logo abaixo | Baixe o `threshold` para perto de `0.7`, e olhe a nota no `--debug` |
| O template nunca casa | O template é maior que a região capturada, então todas as escalas são puladas | Aumente a região, ou diminua o recorte |
| O template nunca casa | O recorte tem fundo sobrando | Corte rente às bordas do glifo |
| O template nunca casa | O fundo do template difere do da tela | Use `invert: true`, ou tire o fundo do recorte |
| O template nunca casa | O alvo na tela tem outro tamanho | Alargue `scale_min`/`scale_max`, aumente `scale_steps` |
| A palavra não é reconhecida como um alvo só | O detector procura uma única imagem | Um template e um perfil por letra ou símbolo |
| O template está lento | Muitas escalas em uma região grande | Baixe o `work_scale` para `0.5` ou `0.35` |

### Desempenho e instalação

| Sintoma | Causa | Correção |
|---|---|---|
| Lento em monitor grande | Bytes demais para varrer | Baixe o `work_scale` para `0.35`, ou use `window` com margem |
| Imprime `Perfil invalido: ...` e sai com código `2` | O perfil está sem um campo, com o tipo errado, ou cita um `detector` ou `pointer.mode` inválido | A mensagem nomeia o campo problemático. Compare com um perfil de exemplo |
| `ModuleNotFoundError` | Dependências faltando, ou pasta errada | `pip install -r requirements.txt`, e rode da pasta do projeto |
| Comando `wolfs-screen-hitter` não encontrado | Pacote não instalado | `pip install -e .`, ou use `python -m wolfs_screen_hitter` |
| A captura falha ou fica lenta | DXGI indisponível | Cai para `mss` sozinha; se as duas falharem, veja se a tela não está bloqueada |

---

## Testes

Dois scripts, sem framework extra. Nenhum dos dois mexe no seu mouse por padrão: as partes que movem o cursor são opt-in.

```bash
python tests/test_local.py
```

Seguro para rodar a qualquer momento. Verifica de forma offline que não existe nenhuma chamada de clique no pacote, que `pyautogui` não é dependência, que os perfis carregam e que detectores, regiões e modos de movimento se comportam. Termina sozinho, com uma linha por verificação.

```bash
python tests/test_local.py --executar
python tests/test_e2e.py --executar
```

Estes mexem no seu mouse e focam uma janela por alguns segundos, então nada acontece sem a flag. Com ela, o `test_local.py` acrescenta as duas verificações de movimento reais, e o `test_e2e.py` monta uma cena com um anel claro e um anel vermelho, abre no visualizador do Windows, captura a tela real por DXGI, confirma que detectou o anel claro e ignorou o vermelho, e move o cursor para o centro do alvo.

Sem a flag, essas verificações aparecem como `[pulado]` e o resto continua sendo verificado. Use `--executar` quando não estiver digitando, porque o cursor vai saltar pela tela.

Mais dois scripts mantêm esta documentação honesta. Não precisam de mouse nem de tela:

```bash
python tests/test_readme.py
python tests/test_readme_citacoes.py
```

O primeiro confere que os dois READMEs têm a mesma estrutura, que todo link interno resolve, e que a instalação é a primeira seção. O segundo confere que todo comando, flag, arquivo, chave de perfil e valor de enum citado nos READMEs existe de fato no código. Se você mexer no código e esquecer a documentação, eles falham.

---

## Privacidade

Tudo roda local. Nenhuma informação sai da máquina, e a captura fica restrita à região que você configurou no perfil.

## Licença

MIT. Veja [LICENSE](LICENSE).
