//! Minimal Italian report-card PDF.
//!
//! Uses the built-in Helvetica font from `printpdf` — no external files —
//! so the binary stays self-contained.

use crate::db::{school_years, votes, Database};
use crate::domain::{average::calc_average, rounding::round_report_card};
use crate::domain::types::GradeType;
use printpdf::{BuiltinFont, Mm, PdfDocument};
use std::collections::BTreeMap;
use std::fs::File;
use std::io::BufWriter;

pub fn export(
    db: &Database,
    term: i32,
    school_year_id: Option<i64>,
    split: bool,
    out_path: &std::path::Path,
) -> anyhow::Result<()> {
    let conn = db.pool().get()?;
    let year_id = school_year_id.or_else(|| {
        school_years::active(&conn)
            .ok()
            .flatten()
            .map(|y| y.id)
    });
    let year_name = match year_id {
        Some(id) => school_years::list(&conn)?
            .into_iter()
            .find(|y| y.id == id)
            .map(|y| y.name)
            .unwrap_or_default(),
        None => String::new(),
    };

    let all = votes::list(
        &conn,
        votes::VoteFilter {
            subject: None,
            school_year_id: year_id,
            term: Some(term),
        },
    )?;

    // Group by subject.
    let mut by_subject: BTreeMap<String, Vec<_>> = BTreeMap::new();
    for v in &all {
        by_subject.entry(v.subject.clone()).or_default().push(v.clone());
    }

    let (doc, page1, layer1) =
        PdfDocument::new("VoteTracker Report Card", Mm(210.0), Mm(297.0), "Layer 1");
    let layer = doc.get_page(page1).get_layer(layer1);
    let title_font = doc.add_builtin_font(BuiltinFont::HelveticaBold)?;
    let body_font = doc.add_builtin_font(BuiltinFont::Helvetica)?;

    // Header.
    layer.use_text("VoteTracker", 18.0, Mm(20.0), Mm(275.0), &title_font);
    layer.use_text(
        format!(
            "Pagella — {}° Quadrimestre — {}",
            term,
            if year_name.is_empty() { "—" } else { &year_name }
        ),
        12.0,
        Mm(20.0),
        Mm(267.0),
        &body_font,
    );
    layer.use_text(
        format!(
            "Generato il {}",
            chrono::Local::now().format("%Y-%m-%d %H:%M")
        ),
        9.0,
        Mm(20.0),
        Mm(261.0),
        &body_font,
    );

    // Table header.
    let mut y = 245.0;
    if split {
        layer.use_text("MATERIA", 10.0, Mm(20.0), Mm(y), &title_font);
        layer.use_text("SCRITTO", 10.0, Mm(100.0), Mm(y), &title_font);
        layer.use_text("ORALE", 10.0, Mm(130.0), Mm(y), &title_font);
        layer.use_text("MEDIA", 10.0, Mm(155.0), Mm(y), &title_font);
        layer.use_text("VOTO", 10.0, Mm(180.0), Mm(y), &title_font);
    } else {
        layer.use_text("MATERIA", 10.0, Mm(20.0), Mm(y), &title_font);
        layer.use_text("MEDIA", 10.0, Mm(140.0), Mm(y), &title_font);
        layer.use_text("VOTO", 10.0, Mm(175.0), Mm(y), &title_font);
    }
    y -= 4.0;
    // Underline.
    layer.use_text(
        "_".repeat(90),
        10.0,
        Mm(20.0),
        Mm(y),
        &body_font,
    );
    y -= 6.0;

    for (subject, vs) in &by_subject {
        let avg = calc_average(vs);
        let rounded = round_report_card(avg);

        let avg_str = if avg > 0.0 { format!("{:.2}", avg) } else { "—".into() };
        let rounded_str = if rounded > 0 { rounded.to_string() } else { "—".into() };

        layer.use_text(subject, 11.0, Mm(20.0), Mm(y), &body_font);

        if split {
            let written: Vec<_> = vs.iter().filter(|v| v.kind == GradeType::Written).cloned().collect();
            let oral: Vec<_> = vs.iter().filter(|v| v.kind == GradeType::Oral).cloned().collect();
            let wa = calc_average(&written);
            let oa = calc_average(&oral);
            layer.use_text(
                if wa > 0.0 { format!("{:.2}", wa) } else { "—".into() },
                11.0,
                Mm(100.0),
                Mm(y),
                &body_font,
            );
            layer.use_text(
                if oa > 0.0 { format!("{:.2}", oa) } else { "—".into() },
                11.0,
                Mm(130.0),
                Mm(y),
                &body_font,
            );
            layer.use_text(&avg_str, 11.0, Mm(155.0), Mm(y), &body_font);
            layer.use_text(&rounded_str, 12.0, Mm(180.0), Mm(y), &title_font);
        } else {
            layer.use_text(&avg_str, 11.0, Mm(140.0), Mm(y), &body_font);
            layer.use_text(&rounded_str, 12.0, Mm(175.0), Mm(y), &title_font);
        }

        y -= 7.5;
        if y < 25.0 {
            break; // single-page for now — v1 is small
        }
    }

    // Footer.
    layer.use_text(
        "Arrotondamento: ≥ 0.5 arrotonda per eccesso.",
        8.0,
        Mm(20.0),
        Mm(15.0),
        &body_font,
    );

    doc.save(&mut BufWriter::new(File::create(out_path)?))?;
    Ok(())
}
