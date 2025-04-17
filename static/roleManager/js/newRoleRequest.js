// تنظیم و راه اندازی select2
$(document).ready(function () {
  $(".select2").select2({
    dir: "rtl",
    allowClear: false,
    selectionCssClass: "never-selected",
    minimumResultsForSearch: 5,
  });
  $("#managerSelect").select2({
    placeholder: "       یک مدیر انتخاب کنید",
  });
  $("#teamSelect").select2({
    placeholder: "یک تیم انتخاب کنید",
  });
});

// بخش تغییر رادیو باتن های (بله، خیر) در قسمت اطلاعات تکمیلی
$(document).ready(function () {
  // دکمه بله ارشد دارد
  $("#hasSuperior_yes_image").on("click", function () {
    $("#hasSuperior_yes_input").prop("checked", true);
    $(this).attr("src", $(this).data("clicked"));
    $("#hasSuperior_no_image").attr(
      "src",
      $("#hasSuperior_no_image").data("default")
    );
  });
  // دکمه خیر ارشد دارد
  $("#hasSuperior_no_image").on("click", function () {
    $("#hasSuperior_no_input").prop("checked", true);
    $(this).attr("src", $(this).data("clicked"));
    $("#hasSuperior_yes_image").attr(
      "src",
      $("#hasSuperior_yes_image").data("default")
    );
  });
  // دکمه بله سطح دارد
  $("#hasLevel_yes_image").on("click", function () {
    $("#hasLevel_yes_input").prop("checked", true);
    $(this).attr("src", $(this).data("clicked"));
    $("#hasLevel_no_image").attr(
      "src",
      $("#hasLevel_no_image").data("default")
    );
  });
  // دکمه خیر سطح دارد
  $("#hasLevel_no_image").on("click", function () {
    $("#hasLevel_no_input").prop("checked", true);
    $(this).attr("src", $(this).data("clicked"));
    $("#hasLevel_yes_image").attr(
      "src",
      $("#hasLevel_yes_image").data("default")
    );
  });
});
// دکمه اضافه کردن تیم که هم آن را تشکیل میدهد و هم اضافه میکند، تکراری بودن آن هم چک میشود
$(document).ready(function () {
  $("#topSide_button").on("click", function () {
    let selectedTeam = $("#teamSelect option:selected");

    if (selectedTeam.val()) {
      const teamCard = createTeamCard(
        (teamCode = selectedTeam.attr("teamCode")),
        (teamName = selectedTeam.val()),
        (imageSrc = selectedTeam.data("image-src"))
      );
      if (isDuplicated(teamCard.attr("teamCode"))) {
        $.confirm({
          title: `❌ تیم انتخاب شده تکراری است`,
          content: `شما نمیتوانید تیم تکراری اضافه کنید`,
          type: "red",
          theme: "modern",
          columnClass: "medium",
          boxWidth: "400px",
          useBootstrap: false,
          buttons: {
            ok: {
              text: "باشه",
              btnClass: "btn-red",
            },
          },
        });
      } else {
        selectedTeam.remove();
        $("#showSelectedTeam_gridContainer")
          .append(teamCard)
          .css("display", "grid");
      }
    } else {
      $.confirm({
        title: `❌ تیم انتخاب نشده است`,
        content: `برای اضافه کردن تیم، باید اول آن را انتخاب کنید.`,
        type: "red",
        theme: "modern",
        columnClass: "medium",
        boxWidth: "400px",
        useBootstrap: false,
        buttons: {
          ok: {
            text: "باشه",
            btnClass: "btn-red",
          },
        },
      });
    }
  });
});

// بخش سابمیت فرم و ارسال آن به سرور
$(document).ready(function () {
  $("#roleRequestForm").on("submit", function (event) {
    event.preventDefault();
    let formData = {
      RoleTitle: $("#roleTitleInput").val().trim(),
      HasLevel: $("#hasLevel_yes_input").is(":checked"),
      HasSuperior: $("#hasSuperior_yes_input").is(":checked"),
      AllowedTeams: [],
    };

    $(".item-card_input").each(function () {
      let teamCode = $(this).attr("teamCode");
      let roleCount = $(this).val();
      formData.AllowedTeams.push({
        TeamCode: teamCode,
        RoleCount: roleCount,
      });
    });

    $.ajax({
      url: window.location.href,
      type: "POST",
      data: JSON.stringify(formData),
      contentType: "application/json",
      headers: {
        "X-CSRFToken": $("meta[name='csrf_holder']").attr("content"),
        "Content-Type": "application/json",
      },
      beforeSend: function () {
        $.LoadingOverlay("show");
      },
      complete: function () {
        $.LoadingOverlay("hide");
      },
      success: function (response) {
        let error = response.Error;
        $.confirm({
          title: error ? "❌ خطا" : "✅ موفقیت",
          content: response.Message,
          type: error ? "red" : "green",
          theme: "modern",
          columnClass: "medium",
          boxWidth: "400px",
          useBootstrap: false,
          buttons: {
            ok: {
              text: "باشه",
              btnClass: error ? "btn-red" : "btn-green",
              action: function () {
                $.LoadingOverlay("show");
                window.location.reload();
              },
            },
          },
        });
      },
      error: function (error) {
        $.confirm({
          title: "❌ خطا در ارتباط",
          content: "خطایی در ارتباط با سرور رخ داده است.",
          type: "red",
          theme: "modern",
          columnClass: "medium",
          boxWidth: "400px",
          useBootstrap: false,
          buttons: {
            ok: {
              text: "باشه",
              btnClass: "btn-red",
            },
          },
        });
      },
    });
  });
});

// ------------------------------------ FUNCTIONS ------------------------------------ //
// ایجاد تیم و ارسال آن برای نشان دادن
function createTeamCard(teamCode = null, teamName = null, imageSrc = null) {
  if (teamCode && teamName && imageSrc) {
    const teamCard = $("<div>").attr({
      class: "team-card",
      teamCode: teamCode,
    });
    const itemCard_iconGroup = $("<div>").attr("class", "item-card_icon-group");
    const itemCard_quantity = $("<div>").attr("class", "item-card_quantity");
    const itemCard_close = $("<div>")
      .attr({ class: "item-card_close", "aria-label": "بستن" })
      .text("X");

    const itemCard_icon = $("<img>").attr({
      src: `${imageSrc}${teamCode}.png`,
      alt: "Team Icon",
      class: "item-card_icon",
    });
    const team_name = $("<p>").attr("class", "subHeaderTitle").text(teamName);

    const inputLabel = $("<label>")
      .attr({
        for: "roleNumberInput",
        class: "subHeaderTitle",
      })
      .text("تعداد :");
    const itemCard_input = $("<input>").attr({
      id: "roleNumberInput",
      type: "number",
      min: "1",
      max: "100",
      value: "1",
      class: "item-card_input",
      teamCode: teamCode,
    });

    itemCard_iconGroup.append(itemCard_icon, team_name);
    itemCard_quantity.append(inputLabel, itemCard_input);
    teamCard.append(itemCard_iconGroup, itemCard_quantity, itemCard_close);
    return teamCard;
  } else {
    $.confirm({
      title: `❌ کد تیم انتخاب نشده است`,
      content: `مشکلی در انتخاب تیم پیش آمده است، دوباره امتحان کنید`,
      type: "red",
      theme: "modern",
      columnClass: "medium",
      boxWidth: "400px",
      useBootstrap: false,
      buttons: {
        ok: {
          text: "باشه",
          btnClass: "btn-red",
        },
      },
    });
  }
}

// چک کردن تیم ها برای جلوگیری از تکراری بودن آن
function isDuplicated(teamCode) {
  let isDuplicate = false;
  $("#showSelectedTeam_gridContainer")
    .children(".team-card")
    .each(function () {
      existingTeamCode = $(this).attr("teamCode");
      if (existingTeamCode == teamCode) {
        isDuplicate = true;
        return true;
      }
    });
  return isDuplicate;
}
