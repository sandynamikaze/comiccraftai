def build_comic_layout(outline, story, images):

    layout = []

    for index, panel in enumerate(outline):

        story_panel = story[index]

        layout.append({
            "panel_number": panel["panel_number"],
            "title": panel["title"],
            "scene_description": panel["scene_description"],
            "image_prompt": panel["image_prompt"],
            "image": images[index],
            "caption": story_panel["caption"],
            "narration": story_panel["narration"],
            "dialogue": story_panel["dialogue"]
        })

    return layout