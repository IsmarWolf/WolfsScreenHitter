# WolfsScreenHitter

Aponta o cursor do mouse para um **alvo visual na tela**, encontrado em tempo real por cor ou por imagem de referência. O clique é sempre seu: o programa só posiciona o cursor, nunca clica.

Duas formas de reconhecer o alvo, ambas configuráveis por um arquivo JSON:

- **`shape`** — acha blobs de uma cor com formato próximo de um círculo. Serve para alvos coloridos, contornos, botões, indicadores.
- **`template`** — localize a imagem de uma letra, símbolo, ícone ou número usando correspondência de template em várias escalas. Serve para ler texto na tela.

Roda em Windows, com o alvo em qualquer área que você escolher: janela específica, área central dessa janela, tela inteira, monitor virtual ou um retângulo fixo.

## Testes

Dois scripts, sem framework extra:

```bash
python tests/test_local.py
```

Verifica de forma offline que não existe nenhuma chamada de clique no pacote, que `pyautogui` não é dependência, que os perfis carregam e que detectores, regiões e modos de movimento se comportam. Termina sozinho, com uma linha por verificação.

```bash
python tests/test_e2e.py
```

Faz o teste de verdade: cria uma cena com um anel claro e um anel vermelho, abre no visualizador do Windows, captura a tela real por DXGI, confirma que detectou o anel claro e ignorou o vermelho, e move o cursor para o centro do alvo. Este teste mexe no seu mouse e abre uma janela por alguns segundos.

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

### Estrutura completa

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

O `margin` é o truque mais útil:many programs draw UI icons near the edges, and `margin: 130` removes them from consideration.

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

Confira a saída de `list-windows` e o `title` no perfil. Títulos precisam bater parcialmente, então `"title": "Roblox"` acha `"Roblox Player"`.

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
