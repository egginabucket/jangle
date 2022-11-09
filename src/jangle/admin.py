from django.contrib import admin

from jangle import models


@admin.register(models.ISOLanguageCodes)
class ISOLanguageCodesAdmin(admin.ModelAdmin):
    list_display = [
        "part_2b",
        "part_2t",
        "part_1",
    ]
    search_fields = [
        "part_1",
        "part_2b",
        "part_2t",
    ]


@admin.register(models.SimpleISOLanguageCollection)
class SimpleISOLanguageCollectionAdmin(admin.ModelAdmin):
    list_display = [
        "part_5",
        "names_en",
    ]
    search_fields = [
        "part_5",
        "names_en",
        "names_fr",
    ]


@admin.register(models.ISOLanguage)
class ISOLanguageAdmin(admin.ModelAdmin):
    list_display = [
        "ref_name",
        "part_3",
        "scope",
        "lang_type",
        "macrolanguage",
    ]
    search_fields = [
        "ref_name",
        "part_3",
        "codes__part_1",
        "codes__part_2b",
        "codes__part_2t",
    ]


@admin.register(models.ISOLanguageName)
class ISOLanguageNameAdmin(admin.ModelAdmin):
    list_display = ["printable", "iso_lang"]
    search_fields = [
        "printable",
        "inverted",
        "iso_lang__part_3",
        "iso_lang__codes__part_1",
        "iso_lang__codes__part_2b",
        "iso_lang__codes__part_2t",
    ]


@admin.register(models.Script)
class ScriptAdmin(admin.ModelAdmin):
    list_display = ["code", "no", "names_en", "pva", "unicode_version", "script_date"]
    search_fields = [
        "code",
        "no",
        "names_en",
        "names_fr",
        "pva",
    ]


@admin.register(models.IANASubtagRegistry)
class IANASubtagRegistryAdmin(admin.ModelAdmin):
    list_display = [
        "file_date",
        "saved",
    ]


@admin.register(models.IANASubtagRecord)
class IANASubtagRecordAdmin(admin.ModelAdmin):
    list_display = [
        "first_description",
        "deprecated",
        "added",
        "pref_value",
    ]
    search_fields = [
        "descriptions__text",
    ]


@admin.register(models.LanguageSubtag)
class LanguageSubtagAdmin(admin.ModelAdmin):
    list_display = ["code", "iana", "scope", "macrolanguage"]
    search_fields = ["code", "iana__descriptions__text"]


@admin.register(models.ExtlangSubtag)
class ExtlangSubtagAdmin(admin.ModelAdmin):
    list_display = ["code", "iana", "scope", "macrolanguage"]
    search_fields = ["code", "iana__descriptions__text"]


@admin.register(models.ScriptSubtag)
class ScriptSubtagAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "ext_data",
        "iana",
    ]
    search_fields = [
        "code",
        "iana__descriptions__text",
    ]


@admin.register(models.RegionSubtag)
class RegionSubtagAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "ext_data",
        "iana",
    ]
    search_fields = [
        "code",
        "iana__descriptions__text",
    ]


@admin.register(models.VariantSubtag)
class VariantSubtagAdmin(admin.ModelAdmin):
    list_display = [
        "text",
        "iana",
    ]
    search_fields = [
        "text",
        "iana__descriptions__text",
    ]


@admin.register(models.LanguageTag)
class LanguageTagAdmin(admin.ModelAdmin):
    list_display = [
        "tag_str",
        "description",
        "iana",
    ]
    search_fields = [
        "lang_tag__code",
        "region_tag__code",
        "script_tag__code",
        "private_tag",
        "private_subtag",
        "grandfathered_tag",
        "iana_subtags__subtag",
    ]
