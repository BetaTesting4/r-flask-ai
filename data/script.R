options(warn=1)
    png("data/output.png")
    .libPaths("r_libs")

install.packages("fs", repos = "https://cloud.r-project.org")
input1 <- "/home/runner/workspace/r_libs/00LOCK-dplyr"
input2 <- TRUE
fs::dir_delete(input1, recurse = input2)