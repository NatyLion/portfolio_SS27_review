# ============================================================
# LIONNA query pieces — the LEFT side of the match.
#   category      : must be one of config.categories keys
#   construction  : LIONNA's intended method (drives the mismatch flag)
#   attrs         : defining features, 0..1 salience (higher = more defining)
# The 3 below are the ones validated in the prototype. Add the rest of SS27.
# ============================================================

- name: Refined Mesh Layer Top
  category: long sleeve
  construction: cut-and-sew
  attrs: {sheer_mesh_panel: 1.0, fitted_sculpt: 1.0, layering: 1.0, crew_neck: 1.0, thumbhole: 0.5, opaque_body: 1.0}

- name: Sculpt Performance Legging
  category: legging
  construction: cut-and-sew
  attrs: {high_waist: 1.0, sculpt_seams: 1.0, no_front_seam: 1.0, squat_proof: 1.0, full_length: 1.0}

- name: Court Longline Polo
  category: polo
  construction: cut-and-sew
  attrs: {polo_collar: 1.0, longline: 1.0, placket: 1.0, court_aesthetic: 1.0}

# ---- add SS27 line below (examples, edit freely) ----
# - name: Work Sculpt Straight Pant
#   category: pant
#   construction: cut-and-sew
#   attrs: {high_waist: 1.0, front_pleat: 1.0, straight_leg: 1.0, hidden_pocket: 0.7, clean_front: 1.0}
# - name: Top Lioness
#   category: tank
#   construction: cut-and-sew
#   attrs: {strappy_back: 1.0, scoop_neck: 0.8, sculpt: 1.0, shelf_bra: 0.8}
