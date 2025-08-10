/* Export BAR_CHART_DAILY_CVES_DB environment variable before running:

export BAR_CHART_DAILY_CVES_DB=<DB username,password and URL*/

package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"strconv"

	"github.com/go-echarts/go-echarts/v2/charts"
	"github.com/go-echarts/go-echarts/v2/opts"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Query database to get unique basescore counts to display on the X-axis
func getUniqueBasescoreCounts(dbPool *pgxpool.Pool) (basecoreCounts []string) {
	rows, err := dbPool.Query(context.Background(), "SELECT COUNT(id), basescore FROM dailycves GROUP BY basescore ORDER BY basescore ASC")
	if err != nil {
		log.Fatal("Could not get basescores from \"dailycves\" table ", err)
	}

	defer rows.Close()

	for rows.Next() {
		var count int
		var basescore float64
		err := rows.Scan(&count, &basescore)
		if err != nil {
			log.Fatal(err)
		}
		// Store only the unique basescores
		basecoreCounts = append(basecoreCounts, strconv.FormatFloat(basescore, 'g', -1, 64))
	}

	return basecoreCounts
}

// Query database to get the counts of each unique basescore to display on the Y-axis
func generateBarItems(dbPool *pgxpool.Pool) []opts.BarData {
	rows, err := dbPool.Query(context.Background(), "SELECT COUNT(id), basescore FROM dailycves GROUP BY basescore ORDER BY basescore ASC")
	if err != nil {
		log.Fatal("Could not get basescores from \"dailycves\" table ", err)
	}

	defer rows.Close()

	items := make([]opts.BarData, 0)
	for rows.Next() {
		var count int
		var basescore float64
		err := rows.Scan(&count, &basescore)
		if err != nil {
			log.Fatal(err)
		}
		// Store only the counts of each unique basescore
		items = append(items, opts.BarData{Value: count})
	}

	return items
}

// HTTP server to display bar chart
func httpserver(w http.ResponseWriter, _ *http.Request) {

	dbPool, err := pgxpool.New(context.Background(), os.Getenv("BAR_CHART_DAILY_CVES_DB"))
	if err != nil {
		log.Fatal("Unable to create connection pool to database ", err)
	}

	defer dbPool.Close()

	bar := charts.NewBar()
	// Set some global options
	bar.SetGlobalOptions(charts.WithTitleOpts(opts.Title{
		Title: "Daily CVE Base Scores By Amount",
		/*TitleStyle: &opts.TextStyle{
			FontSize: 30,
		},*/
	}),
		charts.WithXAxisOpts(opts.XAxis{
			Name:         "Base Score",
			NameLocation: "middle",
			NameGap:      40,
			AxisLabel: &opts.AxisLabel{
				FontSize:   15,
				FontWeight: "bold",
			},
		}),
		charts.WithYAxisOpts(opts.YAxis{
			Name:         "Amount",
			NameLocation: "middle",
			NameGap:      40,
			AxisLabel: &opts.AxisLabel{
				FontSize:   15,
				FontWeight: "bold",
			},
		}),
		charts.WithInitializationOpts(opts.Initialization{
			Width:  "1300px",
			Height: "600px",
		}),
	)

	// Put data into instance
	bar.SetXAxis(getUniqueBasescoreCounts(dbPool)).
		AddSeries("Base Score Amount", generateBarItems(dbPool)).
		SetSeriesOptions(
			charts.WithBarChartOpts(opts.BarChart{
				BarGap: "150%",
			}),
			(charts.WithMarkPointNameTypeItemOpts(
				opts.MarkPointNameTypeItem{Name: "Maximum", Type: "max"},
				opts.MarkPointNameTypeItem{Name: "Minimum", Type: "min"},
			)),
		)

	// Display chart
	bar.Render(w)
}

func main() {
	http.HandleFunc("/", httpserver)
	http.ListenAndServe(":8081", nil)
}
