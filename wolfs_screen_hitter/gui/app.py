"""Janela do WolfsScreenHitter.

Nesta etapa a janela faz o ciclo do perfil: listar, abrir, criar, editar e
salvar. O que e valido continua sendo decidido pelo modelo, entao o que
esta na tela e o mesmo que a CLI le.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .. import profiles
from . import estado as controlador
from . import model
from .widgets import montar_formulario


class Aplicacao(tk.Tk):
    def __init__(self, diretorio=None):
        super().__init__()
        self.geometry("980x640")
        self.minsize(820, 520)

        self.estado = controlador.Estado(diretorio)
        self.caminhos = []
        self.linhas = {}
        # Redesenhar o formulario escreve nos widgets, e escrever num
        # checkbox dispara o evento dele de volta. Sem esta trava, trocar o
        # detector entraria em laco.
        self._reconstruindo = False

        self.mensagem = tk.StringVar()
        self.resumo = tk.StringVar()
        self._montar()
        self.atualizar_lista()

        if self.caminhos:
            self.abrir(self.caminhos[0])
        else:
            self.novo()

        self._atualizar_titulo()

    # -- layout ----------------------------------------------------------

    def _montar(self):
        barra = ttk.Frame(self, padding=(10, 8))
        barra.pack(fill="x")

        for rotulo, comando in (
            ("Novo", self.novo),
            ("Abrir", self.escolher_arquivo),
            ("Salvar", self.salvar),
            ("Salvar como", self.salvar_como),
            ("Atualizar", self.atualizar_lista),
        ):
            ttk.Button(barra, text=rotulo, command=comando).pack(side="left", padx=(0, 6))

        self.resumo_label = ttk.Label(barra, textvariable=self.resumo, anchor="e")
        self.resumo_label.pack(side="right")

        corpo = ttk.PanedWindow(self, orient="horizontal")
        corpo.pack(fill="both", expand=True, padx=10)

        lista = ttk.Frame(corpo, padding=4)
        self.lista = tk.Listbox(lista, width=26, exportselection=False)
        self.lista.pack(fill="both", expand=True)
        self.lista.bind("<<ListboxSelect>>", self._selecionar)
        corpo.add(lista, weight=0)

        # O formulario pode ser mais alto que a janela, entao vai dentro de
        # um canvas com barra de rolagem.
        fora = ttk.Frame(corpo)
        canvas = tk.Canvas(fora, highlightthickness=0, borderwidth=0)
        rolagem = ttk.Scrollbar(fora, orient="vertical", command=canvas.yview)
        self.formulario = ttk.Frame(canvas)
        self.formulario.bind(
            "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.formulario, anchor="nw")
        canvas.configure(yscrollcommand=rolagem.set)
        canvas.pack(side="left", fill="both", expand=True)
        rolagem.pack(side="right", fill="y")
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-e.delta // 120, "units"))
        corpo.add(fora, weight=1)

        self.mensagem_label = ttk.Label(self, textvariable=self.mensagem, anchor="w", padding=(10, 6))
        self.mensagem_label.pack(fill="x")

        ttk.Style(self).configure("Erro.TEntry", fieldbackground="#ffd9d9")

    # -- lista de perfis -------------------------------------------------

    def atualizar_lista(self):
        """Redesenha a lista, mantendo selecionado o perfil aberto."""
        anterior = self.estado.caminho
        self.caminhos = self.estado.listar()
        self.lista.delete(0, tk.END)

        for indice, caminho in enumerate(self.caminhos):
            self.lista.insert(tk.END, caminho.name)
            if caminho == anterior:
                self.lista.selection_set(indice)

    def _selecionar(self, _evento):
        selecao = self.lista.curselection()
        if not selecao:
            return
        caminho = self.caminhos[selecao[0]]
        if caminho != self.estado.caminho:
            self._confirmar_descarte(lambda: self.abrir(caminho))

    def _confirmar_descarte(self, continuar):
        """Nao perde o que foi digitado sem perguntar."""
        if not self.estado.sujo or messagebox.askyesno(
            "Descartar mudancas", "Tem mudanca nao salva. Continuar?"
        ):
            continuar()

    # -- acoes -----------------------------------------------------------

    def novo(self):
        self.estado.novo()
        self._redesenhar()
        self.avisar("Perfil novo. Use Salvar para escolher o nome.")

    def abrir(self, caminho):
        try:
            self.estado.abrir(caminho)
        except profiles.ProfileError as erro:
            self.avisar(str(erro), erro=True)
            return
        self._redesenhar()
        self.avisar(f"Aberto: {Path(caminho).name}")

    def escolher_arquivo(self):
        escolhido = filedialog.askopenfilename(
            title="Abrir perfil",
            initialdir=self.estado.diretorio,
            filetypes=[("Perfis JSON", "*.json")],
        )
        if escolhido:
            self.abrir(Path(escolhido))

    def salvar(self):
        return self.salvar_como() if not self.estado.caminho else self._gravar(self.estado.caminho)

    def salvar_como(self):
        nome = self.estado.texto("name").strip() or "perfil"
        escolhido = filedialog.asksaveasfilename(
            title="Salvar perfil",
            initialdir=self.estado.diretorio,
            initialfile=f"{nome}.json",
            defaultextension=".json",
            filetypes=[("Perfis JSON", "*.json")],
        )
        return self._gravar(Path(escolhido)) if escolhido else None

    def _gravar(self, destino):
        try:
            salvo = self.estado.salvar(destino)
        except model.ErroDeCampo as erro:
            self._marcar(erro.caminho, erro.mensagem)
            return None
        except (controlador.EstadoSemDestino, profiles.ProfileError) as erro:
            messagebox.showerror("Nao deu para salvar", str(erro))
            return None

        self.limpar_erros()
        self.atualizar_lista()
        self.avisar(f"Salvo: {salvo.name}")
        return salvo

    def _marcar(self, caminho, mensagem):
        """Aponta o campo errado, e nao so a mensagem."""
        self.limpar_erros()
        linha = self.linhas.get(caminho)
        if linha:
            linha.marcar_erro(mensagem)
            if hasattr(linha.widget, "focus_set"):
                linha.widget.focus_set()
        self.avisar(f"{caminho}: {mensagem}", erro=True)

    def limpar_erros(self):
        for linha in self.linhas.values():
            linha.limpar_erro()

    # -- formulario ------------------------------------------------------

    def _ao_mudar(self, campo, texto):
        if self._reconstruindo:
            return
        mudou_contexto = self.estado.definir(campo, texto)
        if mudou_contexto:
            self._redesenhar()
        self._atualizar_titulo()

    def _redesenhar(self):
        self._reconstruindo = True
        try:
            for child in self.formulario.winfo_children():
                child.destroy()
            self.linhas = montar_formulario(
                self.formulario, self.estado.campos, self._ao_mudar
            )
        finally:
            self._reconstruindo = False
        self._atualizar_titulo()

    def _atualizar_titulo(self):
        self.title(f"WolfsScreenHitter - {self.estado.rotulo()}")
        self.resumo.set(self.estado.resumo())

    def avisar(self, texto, erro=False):
        self.mensagem.set(texto)
        self.mensagem_label.configure(foreground="#b00020" if erro else "#333333")


def main():
    Aplicacao().mainloop()
