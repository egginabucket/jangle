from django.db import models

from .languages import ISOLanguage


class Region(models.Model):
    names: "models.manager.RelatedManager[RegionName]"

    class Tier(models.IntegerChoices):
        GLOBAL = 0, "global"
        REGIONAL = 1, "regional"
        CONTINENTAL = 2, "continental"
        SUB_REGIONAL = 3, "sub-regional"
        INTERMEDIARY = 4, "intermediary"
        COUNTRY = 5, "country or area"

    tier = models.PositiveSmallIntegerField(choices=Tier.choices)
    no = models.PositiveSmallIntegerField(
        "ISO 3166-1 numeric / UN M.49 code",
        unique=True,
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        on_delete=models.CASCADE,
    )

    @property
    def no_str(self) -> str:
        return "{:03d}".format(self.no)

    def get_name(self, iso_language: ISOLanguage) -> str:
        return self.names.get(iso_language=iso_language).name

    def __str__(self) -> str:
        return self.get_name(ISOLanguage.objects.get_from_ietf("en"))


class RegionName(models.Model):
    region = models.ForeignKey(
        Region,
        related_name="names",
        on_delete=models.CASCADE,
    )
    name = models.TextField(max_length=150)
    iso_lang = models.ForeignKey(
        ISOLanguage,
        on_delete=models.PROTECT,
    )

    class Meta:
        unique_together = ("region", "iso_lang")


class ISORegion(models.Model):
    """ISO 3166 region"""

    region = models.OneToOneField(
        Region,
        related_name="iso",
        on_delete=models.CASCADE,
    )
    alpha_2 = models.CharField(
        "ISO 3166-1 alpha-2 code",
        unique=True,
        max_length=2,
    )
    alpha_3 = models.CharField(
        "ISO 3166-1 alpha-3 code",
        unique=True,
        max_length=3,
    )
    in_ldc = models.BooleanField(
        "Least Developing Countries",
        default=False,
    )
    in_lldc = models.BooleanField(
        "Land Locked Developing Countries",
        default=False,
    )
    in_sids = models.BooleanField(
        "Small Island Developing States",
        default=False,
    )

    def __str__(self) -> str:
        return str(self.region)

    class Meta:
        verbose_name = "ISO 3166 Region"
