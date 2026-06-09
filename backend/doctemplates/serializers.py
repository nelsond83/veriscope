from rest_framework import serializers
from .models import DocumentTemplate, TemplateField


class TemplateFieldSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = TemplateField
        fields = ['id', 'field_name', 'custom_label', 'regex_pattern',
                  'capture_group', 'case_insensitive', 'order']


class DocumentTemplateSerializer(serializers.ModelSerializer):
    fields = TemplateFieldSerializer(many=True)

    class Meta:
        model = DocumentTemplate
        fields = ['id', 'name', 'description', 'keywords', 'sample_text',
                  'fields', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        fields_data = validated_data.pop('fields', [])
        template = DocumentTemplate.objects.create(**validated_data)
        for i, fd in enumerate(fields_data):
            fd.pop('id', None)
            fd.setdefault('order', i)
            TemplateField.objects.create(template=template, **fd)
        return template

    def update(self, instance, validated_data):
        fields_data = validated_data.pop('fields', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if fields_data is not None:
            existing_ids = {str(f.id) for f in instance.fields.all()}
            incoming_ids = {str(f['id']) for f in fields_data if f.get('id')}
            # Remove fields not in the incoming list
            instance.fields.exclude(pk__in=incoming_ids).delete()
            for i, fd in enumerate(fields_data):
                fid = fd.pop('id', None)
                fd.setdefault('order', i)
                if fid and str(fid) in existing_ids:
                    instance.fields.filter(pk=fid).update(**fd)
                else:
                    TemplateField.objects.create(template=instance, **fd)

        instance.refresh_from_db()
        return instance
