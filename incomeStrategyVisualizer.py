import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title  = "Income Strategy Visualizer",
    layout      = "wide",
)

# ---------------------------------------------------
# Color map
# ---------------------------------------------------
COLOR_MAP = {
    "Regular Income Tax":                   "#FF6666",
    "Investment Growth Tax":                "#FFCCCC",
    "Regular401K Tax":                      "#FF9999",
    "Expenses":                             "#FFFF66",
    "Regular401K Contribution":             "#99CCFF",
    "Roth401K Contribution":                "#CCE5FF",
    "BackdoorRoth Contribution":            "#66B2FF",
    "Investment Principal":                 "#CCCCFF",
    "Investment Growth AfterTax":           "#E6FFCC",
    "Regular401K AfterTax":                 "#CCFF99",
    "Roth401K AfterTax":                    "#B3FF66",
    "BackdoorRoth AfterTax":                "#66CC00",
}

# ---------------------------------------------------
# Helpers
# ---------------------------------------------------
def format_currency(x: float) -> str:
    return f"${x:,.0f}"


def make_component_df(parts: dict) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Component":     list(parts.keys()),
            "Amount ($)":    [format_currency(v) for v in parts.values()],
        }
    )


def compute_segment_bounds(parts: dict) -> dict:
    bounds      = {}
    cumulative  = 0.0

    for label, value in parts.items():
        lower               = cumulative
        upper               = cumulative + value
        bounds[label]       = (lower, upper)
        cumulative          = upper

    return bounds


def add_boundary_connector(
    fig,
    left_x,
    right_x,
    left_lower,
    left_upper,
    right_lower,
    right_upper,
    color,
    line_width  = 2,
    line_dash   = "solid",
):
    fig.add_trace(
        go.Scatter(
            x           = [left_x, right_x],
            y           = [left_lower, right_lower],
            mode        = "lines",
            line        = dict(color="rgba(80,80,80,0.7)", width=2.5, dash="solid"),
            showlegend  = False,
            hoverinfo   = "skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x           = [left_x, right_x],
            y           = [left_upper, right_upper],
            mode        = "lines",
            line        = dict(color="rgba(80,80,80,0.7)", width=2.5, dash="solid"),
            showlegend  = False,
            hoverinfo   = "skip",
        )
    )


def collect_all_labels(strategies: list) -> list:
    labels = []
    for strategy in strategies:
        for parts in [strategy["today_parts"], strategy["future_parts"], strategy["keepable_parts"]]:
            for label in parts.keys():
                if label not in labels:
                    labels.append(label)
    return labels


def render_shared_legend(active_labels: list):
    cols = st.columns(6)

    for i, label in enumerate(active_labels):
        color = COLOR_MAP.get(label, "#888888")

        cols[i % 6].markdown(
            f"""
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                <div style="
                    width:14px;
                    height:14px;
                    background-color:{color};
                    border:1px solid rgba(0,0,0,0.30);
                    flex:0 0 14px;
                "></div>
                <div style="font-size:13px; line-height:1.2;">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def make_stacked_chart(
    title:              str,
    today_parts:        dict,
    future_parts:       dict,
    keepable_parts:     dict,
    connector_specs     = None,
    y_axis_max          = None,
    highlight_keepable  = False,
):
    if connector_specs is None:
        connector_specs = []

    fig = go.Figure()

    # Numeric x-positions
    X_TODAY_CENTER       = 0.00
    X_FUTURE_CENTER      = 0.72
    X_KEEPABLE_CENTER    = 1.44
    BAR_WIDTH            = 0.28

    TODAY_RIGHT_EDGE     = X_TODAY_CENTER + BAR_WIDTH / 2
    FUTURE_LEFT_EDGE     = X_FUTURE_CENTER - BAR_WIDTH / 2

    # Preserve order across all three bars
    all_labels = []
    for label in today_parts.keys():
        if label not in all_labels:
            all_labels.append(label)
    for label in future_parts.keys():
        if label not in all_labels:
            all_labels.append(label)
    for label in keepable_parts.keys():
        if label not in all_labels:
            all_labels.append(label)

    # Bars
    for label in all_labels:
        today_value      = today_parts.get(label, 0.0)
        future_value     = future_parts.get(label, 0.0)
        keepable_value   = keepable_parts.get(label, 0.0)

        fig.add_trace(
            go.Bar(
                x               = [X_TODAY_CENTER + 0.015, X_FUTURE_CENTER + 0.015, X_KEEPABLE_CENTER + 0.015],
                y               = [today_value, future_value, keepable_value],
                width           = [BAR_WIDTH, BAR_WIDTH, BAR_WIDTH],
                marker_color    = "rgba(0,0,0,0.08)",
                marker_line     = dict(width=0),
                showlegend      = False,
                hoverinfo       = "skip",
            )
        )

        keepable_line_color   = "rgba(0,0,0,0.25)"
        keepable_line_width   = 1

        if highlight_keepable and keepable_value > 0:
            keepable_line_color = "rgba(20,20,20,0.85)"
            keepable_line_width = 2.5

        fig.add_trace(
            go.Bar(
                name                = label,
                x                   = [X_TODAY_CENTER, X_FUTURE_CENTER, X_KEEPABLE_CENTER],
                y                   = [today_value, future_value, keepable_value],
                width               = [BAR_WIDTH, BAR_WIDTH, BAR_WIDTH],
                marker_color        = COLOR_MAP.get(label, "#888888"),
                opacity             = 0.92,
                marker_line_color   = ["rgba(0,0,0,0.25)", "rgba(0,0,0,0.25)", keepable_line_color],
                marker_line_width   = [1, 1, keepable_line_width],
                legendgroup         = label,
                showlegend          = False,
                text                = [
                    format_currency(today_value) if today_value > 0 else "",
                    format_currency(future_value) if future_value > 0 else "",
                    format_currency(keepable_value) if keepable_value > 0 else "",
                ],
                textposition        = "inside",
                insidetextanchor    = "middle",
                textfont            = dict(size=16, color="#222222"),
                hovertemplate       = f"{label}<br>$%{{y:,.0f}}<extra></extra>",
            )
        )

    # Compute bounds after stacking order is known
    today_bounds     = compute_segment_bounds(today_parts)
    future_bounds    = compute_segment_bounds(future_parts)

    # Boundary connectors
    for spec in connector_specs:
        left_label       = spec["left_label"]
        right_start      = spec["right_start"]
        right_end        = spec["right_end"]
        color            = "#666666",
        line_width       = 3, 
        line_dash        = "solid",

        if left_label in today_bounds and right_start in future_bounds and right_end in future_bounds:
            left_lower, left_upper         = today_bounds[left_label]
            right_lower, _                 = future_bounds[right_start]
            _, right_upper                 = future_bounds[right_end]

            add_boundary_connector(
                fig         = fig,
                left_x      = TODAY_RIGHT_EDGE,
                right_x     = FUTURE_LEFT_EDGE,
                left_lower  = left_lower,
                left_upper  = left_upper,
                right_lower = right_lower,
                right_upper = right_upper,
                color       = color,
                line_width  = line_width,
                line_dash   = line_dash,
            )

    # Add top-of-bar connector once
    total_today  = sum(today_parts.values())
    total_future = sum(future_parts.values())

    add_boundary_connector(
        fig         = fig,
        left_x      = TODAY_RIGHT_EDGE,
        right_x     = FUTURE_LEFT_EDGE,
        left_lower  = total_today,
        left_upper  = total_today,
        right_lower = total_future,
        right_upper = total_future,
        color       = "#666666",
        line_width  = 3, 
        line_dash   = "solid",
    )

    fig.update_layout(
        barmode             = "stack",
        title               = "",
        xaxis_title         = "",
        yaxis_title         = "",
        height              = 500,
        width               = 560,
        margin              = dict(l=0, r=10, t=20, b=20),
        bargap              = 0.25,
        plot_bgcolor        = "#fafafa",
        paper_bgcolor       = "#ffffff",
        font                = dict(size=15),
    )

    fig.update_xaxes(
        tickmode            = "array",
        tickvals            = [X_TODAY_CENTER, X_FUTURE_CENTER, X_KEEPABLE_CENTER],
        ticktext            = ["Today", "Future", "Keep"],
        tickfont            = dict(size=17),
        tickangle           = 0,
        showgrid            = False,
        zeroline            = False,
        range               = [-0.62, 1.72],
    )

    fig.update_yaxes(
        tickfont            = dict(size=14),
        showgrid            = False,
        zeroline            = False,
        showticklabels      = False,
        range               = [0, y_axis_max] if y_axis_max is not None else None,
    )

    # Faint horizontal reference lines
    if y_axis_max is not None:
        if y_axis_max <= 500_000:
            step = 50_000
        elif y_axis_max <= 2_000_000:
            step = 100_000
        else:
            step = 250_000

        current = step
        while current <= y_axis_max:
            fig.add_hline(
                y           = current,
                line_width  = 1,
                line_color  = "rgba(0,0,0,0.08)",
                layer       = "below",
            )

            if current >= 1_000_000:
                label = f"${current/1_000_000:.1f}M"
            else:
                label = f"${current/1_000:.0f}K"

            fig.add_annotation(
                x           = -0.52,
                y           = current,
                text        = label,
                showarrow   = False,
                font        = dict(size=11, color="rgba(0,0,0,0.45)"),
                xanchor     = "left",
                yanchor     = "bottom",
            )

            current += step

    return fig


def render_strategy(
    title: str,
    today_parts: dict,
    future_parts: dict,
    keepable_parts: dict,
    connector_specs: list,
    show_tables: bool,
    y_axis_max: float,
    highlight_keepable: bool,
):
    display_title = title + " ★" if highlight_keepable else title
    st.markdown(
        f"""
        <div style="
            height: 20px;
            font-size: 16px;
            font-weight: 600;
            line-height: 1.05;
            display: flex;
            align-items: flex-start;
            margin-bottom: 6px;
        ">
            {display_title}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if show_tables:
        col_left, col_mid, col_right = st.columns([1, 1, 1])

        with col_left:
            st.caption("Today")
            st.dataframe(
                make_component_df(today_parts),
                hide_index          = True,
                use_container_width = True,
            )

        with col_mid:
            st.caption("Future")
            st.dataframe(
                make_component_df(future_parts),
                hide_index          = True,
                use_container_width = True,
            )

        with col_right:
            st.caption("Keep")
            st.dataframe(
                make_component_df(keepable_parts),
                hide_index          = True,
                use_container_width = True,
            )

    st.plotly_chart(
        make_stacked_chart(
            title               = title,
            today_parts         = today_parts,
            future_parts        = future_parts,
            keepable_parts      = keepable_parts,
            connector_specs     = connector_specs,
            y_axis_max          = y_axis_max,
            highlight_keepable  = highlight_keepable,
        ),
        use_container_width = False,
        theme = None,
    )

# ---------------------------------------------------
# App title
# ---------------------------------------------------
st.title("Income Strategy Visualizer")
st.caption("Explore how gross income today flows through different taxation strategies into the future.")
st.markdown("## Inputs")
st.markdown("**Set the inputs below, then compare the strategies underneath.**")

# ---------------------------------------------------
# Inputs
# ---------------------------------------------------
with st.expander("", expanded=True):

    col1, col2, col3, col4, col5  = st.columns(5)

    with col1:
        income                      = st.slider("Gross Income", 0.0, 1000000.0, 200000.0, step=1000.0)
        expenses                    = st.slider("Annual Expenses", 0.0, income, 100000, step=1000.0)
        show_baseline               = st.checkbox("Baseline", value=True)

    with col2:
        current_tax_rate            = st.slider("Current Tax Rate (%)", 0.0, 50.0, 30.0, step=1.0)
        future_tax_rate             = st.slider("Future Tax Rate (%)", 0.0, 50.0, 25.0, step=1.0)
        show_regular401k            = st.checkbox("Regular401K", value=True)

    with col3:
        investment_rate             = st.slider("Annual Investment Return (%)", 0.0, 15.0, 10.0, step=1.0)
        years                       = st.slider("Years Invested", 1.0, 40.0, 14.0, step=1.0)
        show_roth401k               = st.checkbox("Roth401K", value=True)

    with col4:
        regular401k_limit           = st.slider("Regular 401(k) Limit", 0.0, 30000.0, 23000.0, step=1000.0)
        roth401k_limit              = st.slider("Roth 401(k) Limit", 0.0, 30000.0, 23000.0, step=1000.0)
        show_regular401k_backdoor   = st.checkbox("Regular401K + BackdoorRoth", value=True)
    
    with col5:
        rothBackdoor_limit          = st.slider("Backdoor Roth Limit", 0.0, 90000.0, 70000.0, step=1000.0) 
        capital_gains_tax_rate      = st.slider("Capital Gains Tax Rate (%)", 0.0, 30.0, 20.0, step=1.0)
        show_roth401k_backdoor      = st.checkbox("Roth401K + BackdoorRoth",    value=True)
        show_tables                 = False #st.checkbox("Show tables", value=False)

# ---------------------------------------------------
# Strategy: Baseline
# ---------------------------------------------------
taxable_income                      = income
income_tax                          = taxable_income * current_tax_rate / 100
income_aftertax                     = taxable_income - income_tax
investment_principal                = max(income_aftertax - expenses, 0.0)
investment_future_value             = investment_principal * ((1 + investment_rate / 100) ** years)
investment_growth                   = max(investment_future_value - investment_principal, 0.0)
investment_growth_tax               = investment_growth * capital_gains_tax_rate / 100
investment_growth_aftertax          = investment_growth - investment_growth_tax

baseline_today_parts = {
    "Regular Income Tax":           income_tax,
    "Expenses":                     expenses,
    "Investment Principal":         investment_principal,
}

baseline_future_parts = {
    "Regular Income Tax":           income_tax,
    "Expenses":                     expenses,
    "Investment Principal":         investment_principal,
    "Investment Growth Tax":        investment_growth_tax,
    "Investment Growth AfterTax":   investment_growth_aftertax,
}

baseline_keepable_parts = {
    "Investment Principal":         investment_principal,
    "Investment Growth AfterTax":   investment_growth_aftertax,
}

baseline_connector_specs = [
    {
        "left_label":    "Regular Income Tax",
        "right_start":   "Regular Income Tax",
        "right_end":     "Regular Income Tax",
    },
    {
        "left_label":    "Expenses",
        "right_start":   "Expenses",
        "right_end":     "Expenses",
    },
    {
        "left_label":    "Investment Principal",
        "right_start":   "Investment Principal",
        "right_end":     "Investment Growth AfterTax",
    },
]

# ---------------------------------------------------
# Strategy: Regular 401K
# ---------------------------------------------------
contribution_regular401k            = min(regular401k_limit, income - expenses)
contribution_regular401k            = max(contribution_regular401k, 0.0) 
taxable_income                      = income - contribution_regular401k

income_tax                          = taxable_income * current_tax_rate / 100
income_aftertax                     = taxable_income - income_tax

investment_principal                = max(income_aftertax - expenses, 0.0)
investment_future_value             = investment_principal * ((1 + investment_rate / 100) ** years)
investment_growth                   = max(investment_future_value - investment_principal, 0.0)
investment_growth_tax               = investment_growth * capital_gains_tax_rate / 100
investment_growth_aftertax          = investment_growth - investment_growth_tax

regular401k_future_value            = contribution_regular401k * ((1 + investment_rate / 100) ** years)
regular401k_tax                     = regular401k_future_value * future_tax_rate / 100
regular401k_aftertax                = regular401k_future_value - regular401k_tax

regular401k_today_parts = {
    "Regular Income Tax":           income_tax,
    "Expenses":                     expenses,
    "Investment Principal":         investment_principal,
    "Regular401K Contribution":     contribution_regular401k,
}

regular401k_future_parts = {
    "Regular Income Tax":           income_tax,
    "Expenses":                     expenses,
    "Investment Principal":         investment_principal,
    "Investment Growth Tax":        investment_growth_tax,
    "Investment Growth AfterTax":   investment_growth_aftertax,
    "Regular401K Tax":              regular401k_tax,
    "Regular401K AfterTax":         regular401k_aftertax,
}

regular401k_keepable_parts = {
    "Investment Principal":         investment_principal,
    "Investment Growth AfterTax":   investment_growth_aftertax,
    "Regular401K AfterTax":         regular401k_aftertax,
}

regular401k_connector_specs = [
    {
        "left_label":    "Regular Income Tax",
        "right_start":   "Regular Income Tax",
        "right_end":     "Regular Income Tax",
    },
    {
        "left_label":    "Expenses",
        "right_start":   "Expenses",
        "right_end":     "Expenses",
    },
    {
        "left_label":    "Investment Principal",
        "right_start":   "Investment Principal",
        "right_end":     "Investment Growth AfterTax",
    },
    {
        "left_label":    "Regular401K Contribution",
        "right_start":   "Regular401K Tax",
        "right_end":     "Regular401K AfterTax",
    },
]

# ---------------------------------------------------
# Strategy: Roth 401K
# ---------------------------------------------------
taxable_income                      = income
income_tax                          = taxable_income * current_tax_rate / 100
income_aftertax                     = taxable_income - income_tax
contribution_roth401k               = min(roth401k_limit, income_aftertax - expenses)
contribution_roth401k               = max(contribution_roth401k, 0.0) 

investment_principal                = income_aftertax - expenses - contribution_roth401k
investment_future_value             = investment_principal * ((1 + investment_rate / 100) ** years)
investment_growth                   = max(investment_future_value - investment_principal, 0.0)
investment_growth_tax               = investment_growth * capital_gains_tax_rate / 100
investment_growth_aftertax          = investment_growth - investment_growth_tax

roth_future_value                   = contribution_roth401k * ((1 + investment_rate / 100) ** years)

roth_today_parts = {
    "Regular Income Tax":           income_tax,
    "Expenses":                     expenses,
    "Investment Principal":         investment_principal,
    "Roth401K Contribution":        contribution_roth401k,
}

roth_future_parts = {
    "Regular Income Tax":           income_tax,
    "Expenses":                     expenses,
    "Investment Principal":         investment_principal,
    "Investment Growth Tax":        investment_growth_tax,
    "Investment Growth AfterTax":   investment_growth_aftertax,
    "Roth401K AfterTax":            roth_future_value,
}

roth_keepable_parts = {
    "Investment Principal":         investment_principal,
    "Investment Growth AfterTax":   investment_growth_aftertax,
    "Roth401K AfterTax":            roth_future_value,
}

roth_connector_specs = [
    {
        "left_label":    "Regular Income Tax",
        "right_start":   "Regular Income Tax",
        "right_end":     "Regular Income Tax",
    },
    {
        "left_label":    "Expenses",
        "right_start":   "Expenses",
        "right_end":     "Expenses",
    },
    {
        "left_label":    "Investment Principal",
        "right_start":   "Investment Principal",
        "right_end":     "Investment Growth AfterTax",
    },
    {
        "left_label":    "Roth401K Contribution",
        "right_start":   "Roth401K AfterTax",
        "right_end":     "Roth401K AfterTax",
    },
]

# ---------------------------------------------------
# Strategy: Regular 401K + Backdoor Roth
# ---------------------------------------------------
contribution_regular401k            = min(regular401k_limit, income - expenses)
contribution_regular401k            = max(contribution_regular401k, 0.0)
taxable_income                      = income - contribution_regular401k
income_tax                          = taxable_income * current_tax_rate / 100
income_aftertax                     = taxable_income - income_tax
cash_after_expenses                 = max(income_aftertax - expenses, 0.0)
backdoor_contribution_roth401k      = min(rothBackdoor_limit - contribution_regular401k, cash_after_expenses)

investment_principal                = max(cash_after_expenses - backdoor_contribution_roth401k, 0.0)
investment_future_value             = investment_principal * ((1 + investment_rate / 100) ** years)
investment_growth                   = max(investment_future_value - investment_principal, 0.0)
investment_growth_tax               = investment_growth * capital_gains_tax_rate / 100
investment_growth_aftertax          = investment_growth - investment_growth_tax

regular401k_future_value            = contribution_regular401k * ((1 + investment_rate / 100) ** years)
regular401k_tax                     = regular401k_future_value * future_tax_rate / 100
regular401k_aftertax                = regular401k_future_value - regular401k_tax

backdoor_roth_future_value          = backdoor_contribution_roth401k * ((1 + investment_rate / 100) ** years)

regular401k_backdoor_today_parts = {
    "Regular Income Tax":           income_tax,
    "Expenses":                     expenses,
    "Investment Principal":         investment_principal,
    "Regular401K Contribution":     contribution_regular401k,
    "BackdoorRoth Contribution":    backdoor_contribution_roth401k,
}

regular401k_backdoor_future_parts = {
    "Regular Income Tax":           income_tax,
    "Expenses":                     expenses,
    "Investment Principal":         investment_principal,
    "Investment Growth Tax":        investment_growth_tax,
    "Investment Growth AfterTax":   investment_growth_aftertax,
    "Regular401K Tax":              regular401k_tax,
    "Regular401K AfterTax":         regular401k_aftertax,
    "BackdoorRoth AfterTax":        backdoor_roth_future_value,
}

regular401k_backdoor_keepable_parts = {
    "Investment Principal":         investment_principal,
    "Investment Growth AfterTax":   investment_growth_aftertax,
    "Regular401K AfterTax":         regular401k_aftertax,
    "BackdoorRoth AfterTax":        backdoor_roth_future_value,
}

regular401k_backdoor_connector_specs = [
    {
        "left_label":    "Regular Income Tax",
        "right_start":   "Regular Income Tax",
        "right_end":     "Regular Income Tax",
    },
    {
        "left_label":    "Expenses",
        "right_start":   "Expenses",
        "right_end":     "Expenses",
    },
    {
        "left_label":    "Investment Principal",
        "right_start":   "Investment Principal",
        "right_end":     "Investment Growth AfterTax",
    },
    {
        "left_label":    "Regular401K Contribution",
        "right_start":   "Regular401K Tax",
        "right_end":     "Regular401K AfterTax",
    },
    {
        "left_label":    "BackdoorRoth Contribution",
        "right_start":   "BackdoorRoth AfterTax",
        "right_end":     "BackdoorRoth AfterTax",
    },
]

# ---------------------------------------------------
# Strategy: Roth 401K + Backdoor Roth
# ---------------------------------------------------
taxable_income                              = income
income_tax                                  = taxable_income * current_tax_rate / 100
income_aftertax                             = taxable_income - income_tax
contribution_roth401k                       = min(roth401k_limit, income_aftertax - expenses) 
contribution_roth401k                       = max(contribution_roth401k, 0.0) 

cash_after_expenses_and_roth                = max(income_aftertax - expenses - contribution_roth401k, 0.0)
backdoor_contribution_roth401k              = min(rothBackdoor_limit - contribution_roth401k, cash_after_expenses_and_roth)

investment_principal                        = max(cash_after_expenses_and_roth - backdoor_contribution_roth401k, 0.0)
investment_future_value                     = investment_principal * ((1 + investment_rate / 100) ** years)
investment_growth                           = max(investment_future_value - investment_principal, 0.0)
investment_growth_tax                       = investment_growth * capital_gains_tax_rate / 100
investment_growth_aftertax                  = investment_growth - investment_growth_tax

roth_future_value                           = contribution_roth401k * ((1 + investment_rate / 100) ** years)
backdoor_roth_future_value                  = backdoor_contribution_roth401k * ((1 + investment_rate / 100) ** years)

roth401k_backdoor_today_parts = {
    "Regular Income Tax":                   income_tax,
    "Expenses":                             expenses,
    "Investment Principal":                 investment_principal,
    "Roth401K Contribution":                contribution_roth401k,
    "BackdoorRoth Contribution":            backdoor_contribution_roth401k,
}

roth401k_backdoor_future_parts = {
    "Regular Income Tax":                   income_tax,
    "Expenses":                             expenses,
    "Investment Principal":                 investment_principal,
    "Investment Growth Tax":                investment_growth_tax,
    "Investment Growth AfterTax":           investment_growth_aftertax,
    "Roth401K AfterTax":                    roth_future_value,
    "BackdoorRoth AfterTax":                backdoor_roth_future_value,
}

roth401k_backdoor_keepable_parts = {
    "Investment Principal":                 investment_principal,
    "Investment Growth AfterTax":           investment_growth_aftertax,
    "Roth401K AfterTax":                    roth_future_value,
    "BackdoorRoth AfterTax":                backdoor_roth_future_value,
}

roth401k_backdoor_connector_specs = [
    {
        "left_label":    "Regular Income Tax",
        "right_start":   "Regular Income Tax",
        "right_end":     "Regular Income Tax",
    },
    {
        "left_label":    "Expenses",
        "right_start":   "Expenses",
        "right_end":     "Expenses",
    },
    {
        "left_label":    "Investment Principal",
        "right_start":   "Investment Principal",
        "right_end":     "Investment Growth AfterTax",
    },
    {
        "left_label":    "Roth401K Contribution",
        "right_start":   "Roth401K AfterTax",
        "right_end":     "Roth401K AfterTax",
    },
    {
        "left_label":    "BackdoorRoth Contribution",
        "right_start":   "BackdoorRoth AfterTax",
        "right_end":     "BackdoorRoth AfterTax",
    },
]

# ---------------------------------------------------
# Y-axis normalization across selected strategies
# ---------------------------------------------------
selected_strategy_heights = []

if show_baseline:
    selected_strategy_heights.append(sum(baseline_today_parts.values()))
    selected_strategy_heights.append(sum(baseline_future_parts.values()))
    selected_strategy_heights.append(sum(baseline_keepable_parts.values()))

if show_regular401k:
    selected_strategy_heights.append(sum(regular401k_today_parts.values()))
    selected_strategy_heights.append(sum(regular401k_future_parts.values()))
    selected_strategy_heights.append(sum(regular401k_keepable_parts.values()))

if show_roth401k:
    selected_strategy_heights.append(sum(roth_today_parts.values()))
    selected_strategy_heights.append(sum(roth_future_parts.values()))
    selected_strategy_heights.append(sum(roth_keepable_parts.values()))

if show_regular401k_backdoor:
    selected_strategy_heights.append(sum(regular401k_backdoor_today_parts.values()))
    selected_strategy_heights.append(sum(regular401k_backdoor_future_parts.values()))
    selected_strategy_heights.append(sum(regular401k_backdoor_keepable_parts.values()))

if show_roth401k_backdoor:
    selected_strategy_heights.append(sum(roth401k_backdoor_today_parts.values()))
    selected_strategy_heights.append(sum(roth401k_backdoor_future_parts.values()))
    selected_strategy_heights.append(sum(roth401k_backdoor_keepable_parts.values()))

GLOBAL_Y_AXIS_MAX = max(selected_strategy_heights) * 1.05 if selected_strategy_heights else 1.0

# ---------------------------------------------------
# Display selected strategies
# ---------------------------------------------------
selected_strategies = []

if show_baseline:
    selected_strategies.append(
        {
            "title":            "Baseline",
            "today_parts":      baseline_today_parts,
            "future_parts":     baseline_future_parts,
            "keepable_parts":   baseline_keepable_parts,
            "connector_specs":  baseline_connector_specs,
        }
    )

if show_regular401k:
    selected_strategies.append(
        {
            "title":            "Regular 401K",
            "today_parts":      regular401k_today_parts,
            "future_parts":     regular401k_future_parts,
            "keepable_parts":   regular401k_keepable_parts,
            "connector_specs":  regular401k_connector_specs,
        }
    )

if show_roth401k:
    selected_strategies.append(
        {
            "title":            "Roth 401K",
            "today_parts":      roth_today_parts,
            "future_parts":     roth_future_parts,
            "keepable_parts":   roth_keepable_parts,
            "connector_specs":  roth_connector_specs,
        }
    )

if show_regular401k_backdoor:
    selected_strategies.append(
        {
            "title":            "Regular 401K + Backdoor Roth",
            "today_parts":      regular401k_backdoor_today_parts,
            "future_parts":     regular401k_backdoor_future_parts,
            "keepable_parts":   regular401k_backdoor_keepable_parts,
            "connector_specs":  regular401k_backdoor_connector_specs,
        }
    )

if show_roth401k_backdoor:
    selected_strategies.append(
        {
            "title":            "Roth 401K + Backdoor Roth",
            "today_parts":      roth401k_backdoor_today_parts,
            "future_parts":     roth401k_backdoor_future_parts,
            "keepable_parts":   roth401k_backdoor_keepable_parts,
            "connector_specs":  roth401k_backdoor_connector_specs,
        }
    )

# ---------------------------------------------------
# Winning strategy based on Keepable bar total
# ---------------------------------------------------
winning_strategy_title = None

if len(selected_strategies) > 0:
    winning_strategy_title = max(
        selected_strategies,
        key=lambda s: sum(s["keepable_parts"].values())
    )["title"]

if len(selected_strategies) == 0:
    st.warning("Select at least one strategy in the Inputs section.")
else:
    st.markdown("## Charts")
    st.markdown("**The starred strategy provides the maximum gain.**")
    cols = st.columns(len(selected_strategies))

    for col, strategy in zip(cols, selected_strategies):
        with col:
            render_strategy(
                title               = strategy["title"],
                today_parts         = strategy["today_parts"],
                future_parts        = strategy["future_parts"],
                keepable_parts      = strategy["keepable_parts"],
                connector_specs     = strategy["connector_specs"],
                show_tables         = show_tables,
                y_axis_max          = GLOBAL_Y_AXIS_MAX,
                highlight_keepable  = (strategy["title"] == winning_strategy_title),
            )

    preferred_order = [
        "Regular Income Tax",
        "Expenses",
        "Investment Principal",
        "Regular401K Contribution",
        "Roth401K Contribution",
        "BackdoorRoth Contribution",
        "Investment Growth Tax",
        "Investment Growth AfterTax",
        "Regular401K Tax",
        "Regular401K AfterTax",
        "Roth401K AfterTax",
        "BackdoorRoth AfterTax",
    ]

    labels_present = collect_all_labels(selected_strategies)
    all_labels = [label for label in preferred_order if label in labels_present]
    st.markdown("**Legend**")
    render_shared_legend(all_labels)