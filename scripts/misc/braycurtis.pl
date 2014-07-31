#! /usr/bin/perl
# Reads in CSV file and computes bray curtis dissimilarity values
# Outputs for min, lower quartile, median, upper quartile, max, and outliers

use strict;
use warnings;
sub bray($$);
sub stats($);

my $csv = shift or die "Usage: perl $0 <input>\n";
open FH, "<", $csv;
my $h = <FH>;
chomp $h;
my @filedata;
while (my $line = <FH>) {
  chomp $line;
  my @arr = split(",", $line);
  foreach (my $i = 1; $i < scalar @arr; $i++) {
    push(@{$filedata[$i-1]}, $arr[$i]);
  }
}
close FH;
my @results;
for (my $i = 0; $i < $#filedata; $i++) {
   for (my $j = $i+1; $j <= $#filedata; $j++) {
      push @results, bray($filedata[$i], $filedata[$j]);
   }
}

my @sorted = sort {$a <=> $b} @results;
stats(\@sorted);

#Subrountine
sub bray($$) {
  my ($arr1, $arr2) = @_;
  my $len = scalar @{$arr2} - 1;
  my ($minsum, $sa, $sb) = 0;
  foreach my $i (0..$len) {
     $sa+=$arr1->[$i];
     $sb+=$arr2->[$i];
     if ($arr1->[$i] < $arr2->[$i]) { $minsum+=$arr1->[$i]} else {$minsum+=$arr2->[$i]}
     #printf "%-15s\t%-15s\t%-15s\n", "$arr1->[$i]($sa)", "$arr2->[$i]($sb)", "$minsum";
  }
  my $bray = 1-(2*($minsum/($sa+$sb)));
  return $bray;
}

sub stats($) {
  my @arr = @{$_[0]};
  my $n = scalar @arr;
  my $lc = ($n+1)*0.25;
  my $med = ($n+1)*0.5;
  my $uc = ($n+1)*0.75;
  my $iqr = $arr[$uc]-$arr[$lc];
  my $minthresh = $arr[$lc]-$iqr;
  my $maxthresh = $arr[$uc]+$iqr;
  my $min = -1;
  my $max = 2;
  my $i = 0;
  my @outliers;
  while ($min < $minthresh) {
    if ($min ne -1) {push @outliers, $min}
    $min = $arr[$i];
    $i++;
  }
  if ($maxthresh >= 1) {
     $max = $arr[-1];
  } else {
     $i = -1;
     while ($max > $maxthresh) {
         if ($min ne 2) {push @outliers, $min}
         $max = $arr[$i];
         $i--;
     }
  } 
  print "$min,$arr[$lc],$arr[$med],$arr[$uc],$max\n";
  print join(",", @outliers); print "\n";
}
