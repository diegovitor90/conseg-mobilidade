from datetime import date, datetime, time, timedelta

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Reserva, Veiculo


INPUT_CLASSES = (
    "mt-2 block w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 "
    "text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 "
    "hover:border-slate-300 focus:border-cyan-500 focus:ring-4 focus:ring-cyan-500/10"
)


def gerar_slots_horarios(inicio='06:00', fim='22:00', intervalo=30):
    inicio_dt = datetime.strptime(inicio, "%H:%M")
    fim_dt = datetime.strptime(fim, "%H:%M")
    slots = []
    atual = inicio_dt
    while atual < fim_dt:
        slots.append(atual.strftime("%H:%M"))
        atual += timedelta(minutes=intervalo)
    return slots


def listar_horarios_disponiveis(data, veiculo_id=None, motorista_id=None, excluir=None):
    horarios = gerar_slots_horarios()
    if not data:
        return [(horario, horario) for horario in horarios]

    if isinstance(data, str):
        try:
            data = date.fromisoformat(data)
        except ValueError:
            return [(horario, horario) for horario in horarios]

    conflitos = set()
    qs = Reserva.objects.filter(data=data)
    if veiculo_id:
        qs = qs.filter(veiculo_id=veiculo_id)
    if motorista_id:
        qs = qs.filter(motorista_id=motorista_id)

    for reserva in qs:
        slot = datetime.combine(data, reserva.horario_saida)
        fim = datetime.combine(data, reserva.horario_retorno)
        while slot < fim:
            conflitos.add(slot.strftime("%H:%M"))
            slot += timedelta(minutes=30)

    if excluir:
        conflitos.update(excluir)

    return [(horario, horario) for horario in horarios if horario not in conflitos]


class VeiculoForm(forms.ModelForm):
    """Padrão adaptado do VeiculoForm da Oficina; sem campos de clientes."""
    class Meta:
        model = Veiculo
        fields = ["codigo", "categoria", "ativo"]
        widgets = {
            "codigo": forms.TextInput(attrs={
                "placeholder": "Ex.: VL-01",
                "autocomplete": "off",
                "autocapitalize": "characters",
                "class": INPUT_CLASSES,
            }),
            "categoria": forms.Select(attrs={"class": INPUT_CLASSES}),
            "ativo": forms.CheckboxInput(attrs={
                "class": "size-5 rounded-md border-slate-300 text-cyan-600 focus:ring-cyan-500",
            }),
        }
        help_texts = {
            "codigo": "Identificação única, com até 10 caracteres. Letras são salvas em maiúsculas.",
            "categoria": "A categoria define a capacidade automaticamente no servidor.",
            "ativo": "Um veículo ativo pode receber reservas, desde que não haja conflito de horário.",
        }
        error_messages = {
            "codigo": {"unique": "Já existe um veículo com este código.", "required": "Informe o código do veículo."},
            "categoria": {"required": "Selecione uma categoria."},
        }

    def clean_codigo(self):
        return self.cleaned_data["codigo"].strip().upper()


class EntrarForm(AuthenticationForm):
    username = forms.CharField(label="Usuário", widget=forms.TextInput(attrs={
        "autofocus": True,
        "autocomplete": "username",
        "placeholder": "Digite seu usuário",
        "class": INPUT_CLASSES,
    }))
    password = forms.CharField(label="Senha", strip=False, widget=forms.PasswordInput(attrs={
        "autocomplete": "current-password",
        "placeholder": "Digite sua senha",
        "class": INPUT_CLASSES,
    }))


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = [
            "solicitante",
            "setor",
            "atividade",
            "origem",
            "destino",
            "data",
            "horario_saida",
            "horario_retorno",
            "quantidade_passageiros",
            "motorista",
            "observacoes",
        ]
        widgets = {
            "solicitante": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Nome do solicitante"}),
            "setor": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Setor"}),
            "atividade": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Atividade"}),
            "origem": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Origem"}),
            "destino": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Destino"}),
            "data": forms.DateInput(attrs={"type": "date", "class": INPUT_CLASSES}),
            "quantidade_passageiros": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 1, "max": 18}),
            "motorista": forms.Select(attrs={"class": INPUT_CLASSES}),
            "observacoes": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 3, "placeholder": "Observações"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data_atual = self.data.get("data") or getattr(self.instance, "data", None)
        veiculo_id = self.data.get("veiculo") or getattr(self.instance, "veiculo_id", None)
        motorista_id = self.data.get("motorista") or getattr(self.instance, "motorista_id", None)

        horarios = [(horario, horario) for horario in gerar_slots_horarios()]
        self.fields["horario_saida"] = forms.ChoiceField(
            choices=[("", "Selecione o horário de saída")] + horarios,
            widget=forms.Select(attrs={"class": INPUT_CLASSES}),
            label="Horário de saída",
        )
        self.fields["horario_retorno"] = forms.ChoiceField(
            choices=[("", "Selecione o horário de retorno")] + horarios,
            widget=forms.Select(attrs={"class": INPUT_CLASSES}),
            label="Horário de retorno",
        )

        if self.instance and self.instance.horario_saida:
            self.fields["horario_saida"].initial = self.instance.horario_saida.strftime("%H:%M")
        if self.instance and self.instance.horario_retorno:
            self.fields["horario_retorno"].initial = self.instance.horario_retorno.strftime("%H:%M")

    def clean(self):
        cleaned_data = super().clean()
        saida = cleaned_data.get("horario_saida")
        retorno = cleaned_data.get("horario_retorno")
        data = cleaned_data.get("data")
        veiculo = cleaned_data.get("veiculo")
        motorista = cleaned_data.get("motorista")

        if isinstance(saida, str):
            saida = time.fromisoformat(saida)
            cleaned_data["horario_saida"] = saida
        if isinstance(retorno, str):
            retorno = time.fromisoformat(retorno)
            cleaned_data["horario_retorno"] = retorno

        if saida and retorno:
            if retorno <= saida:
                raise forms.ValidationError("O horário de retorno precisa ser posterior ao horário de saída.")

        if data and veiculo and saida and retorno:
            reservas_conflitantes = Reserva.objects.filter(data=data).filter(
                veiculo_id=veiculo.pk,
            )
            if self.instance and self.instance.pk:
                reservas_conflitantes = reservas_conflitantes.exclude(pk=self.instance.pk)

            for reserva in reservas_conflitantes:
                if not (retorno <= reserva.horario_saida or saida >= reserva.horario_retorno):
                    raise forms.ValidationError(
                        "Escolha outro horário. Este veículo já está reservado no período de "
                        f"{reserva.horario_saida} até {reserva.horario_retorno}."
                    )

        if data and motorista and saida and retorno:
            reservas_conflitantes = Reserva.objects.filter(data=data).filter(
                motorista_id=motorista.pk,
            )
            if self.instance and self.instance.pk:
                reservas_conflitantes = reservas_conflitantes.exclude(pk=self.instance.pk)

            for reserva in reservas_conflitantes:
                if not (retorno <= reserva.horario_saida or saida >= reserva.horario_retorno):
                    raise forms.ValidationError(
                        "Escolha outro horário. Este motorista já está reservado no período de "
                        f"{reserva.horario_saida} até {reserva.horario_retorno}."
                    )

        return cleaned_data
