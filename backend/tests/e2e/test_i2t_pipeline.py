from app.schemas import I2TAnalysisResult


def test_i2t_schema_contract():
    model = I2TAnalysisResult(
        style_template='x',
        composition_notes='y',
        color_palette_extracted={'dominant': []},
        style_tags=['tag'],
        mood_keywords=['mood'],
        lighting_description='soft',
    )
    assert model.style_template == 'x'
