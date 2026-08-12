from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')

        email = self.normalize_email(email).lower()
        extra_fields.setdefault('perfil', Usuario.Perfil.CLIENTE)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('perfil', Usuario.Perfil.ADMINISTRADOR)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('O superusuário precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('O superusuário precisa ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Perfil(models.TextChoices):
        CLIENTE = 'CLIENTE', 'Cliente'
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'

    id_usuario = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20)
    password = models.CharField('senha', max_length=128, db_column='senha')
    foto_perfil = models.URLField(max_length=500, blank=True)
    matricula_institucional = models.CharField(max_length=50, blank=True)
    cargo_funcao = models.CharField(max_length=100, blank=True)
    perfil = models.CharField(
        max_length=13,
        choices=Perfil.choices,
        default=Perfil.CLIENTE,
    )
    is_active = models.BooleanField('ativo', default=True)
    is_staff = models.BooleanField('acesso ao admin', default=False)
    date_joined = models.DateTimeField('data de cadastro', default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ('nome_completo', 'cpf', 'telefone')

    class Meta:
        db_table = 'usuario'
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'
        ordering = ('nome_completo',)

    def __str__(self):
        return self.nome_completo

    def get_full_name(self):
        return self.nome_completo

    def get_short_name(self):
        return self.nome_completo.split()[0]

    @property
    def senha(self):
        """Alias compatível com o nome usado no diagrama ER."""
        return self.password

    @senha.setter
    def senha(self, valor):
        self.password = valor

    def definir_senha(self, senha):
        self.set_password(senha)

    def verificar_senha(self, senha):
        return self.check_password(senha)
