# Get Daily CVEs

Technologies used: *Golang, PostgreSQL (Neon), go-echarts*
&nbsp;
For my first Data Engineering project I decided to be contrarian and use Golang instead of the commonly used Python to extract the basescores of CVEs from the NIST CVE API and display them using go-echarts.

I tried using the Golang Gota Dataframe library but I found that [it can't process nested structs](https://github.com/go-gota/gota/issues/163) which I needed for this project. Lack of Dataframe support in Golang will limit my Data Engineering learning and project work so for most projects I will be using Python going forward.

## get_daily_cves.go

The ```get_daily_cves.go``` file reads from the NIST CVE API and stored as list of CVEs in a PostgreSQL database. The program is designed to be run two times a day and when it clears the database by dropping the dailycves table when run on a subsequent day.

The ```bar_chart_daily_cves.go``` program displays the basescores of the CVEs and the amount of each score (score of "0" means that either the NIST determined that the CVE was invalid or that a basescore was not found.)

Programs can be run using:

Export ```GET_DAILY_CVES_DB``` environment variable.

Example (for Neon): ```export GET_DAILY_CVES_DB=postgresql://${Neon username}:${database URL}```

    go run get_daily_cves.go

&nbsp;

Export ```BAR_CHART_DAILY_CVES_DB``` environment variable.

Example (for Neon): ```export BAR_CHART_DAILY_CVES_DB=postgresql://${Neon username}:${database URL}```

    go run bar_chart_daily_cves.go
&nbsp;

Browse to ```http://localhost:8081/``` to see the visualization.

## Demo

![](Get_Daily_CVEs_Demo__2025-08-09-23-03-05.gif)