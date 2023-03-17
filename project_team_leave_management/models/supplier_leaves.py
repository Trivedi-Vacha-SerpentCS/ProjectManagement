# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SupplierLeaves(models.Model):
    _name = "supplier.leaves"
    _description = "Supplier Leaves"
    _rec_name = "partner_id"

    @api.depends("date_from", "date_to")
    def _compute_leave_duration(self):
        """
        Compute the days Duration.
        """
        leave_duration = 0
        for leaves in self:
            if leaves.date_from and leaves.date_to:
                leave_duration = 1 + (leaves.date_to - leaves.date_from).days
            leaves.leave_duration = leave_duration

    def _get_partner_domain(self):
        """
        Get the Partner domain to limit only
        to a supplier compnay's resources.
        """
        domain = []
        if self.env.user.supplier_company_id:
            domain.append(("id", "in", self.env.user.supplier_company_id.child_ids.ids))
        return domain

    parent_id = fields.Many2one(
        related="partner_id.parent_id", string="Related Company"
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Team Member",
        default=lambda self: self.env.user.partner_id,
        domain=lambda self: self._get_partner_domain(),
        required=True,
    )
    subject = fields.Char("Subject", required=True)
    description = fields.Text("Description")
    date_from = fields.Date("From")
    date_to = fields.Date("To")
    leave_duration = fields.Float(
        "Days Duration", compute="_compute_leave_duration", store=True
    )

    @api.constrains("date_from")
    def _check_start_date(self):
        """
        Validate if the Date is of the future only.

        Raises:
            ValidationError: If the Date is not of the Future.
        """
        current_date = fields.Date.today()
        for supp_leaves in self:
            if supp_leaves.date_from < current_date:
                raise ValidationError(
                    _("Start date must be greater than current date!")
                )

    @api.constrains("date_from", "date_to")
    def _check_end_date(self):
        """
        Check if the start date is not greater than end date.

        Raises:
            ValidationError: If the Start date is greater the End date.
        """
        for supp_leaves in self:
            if supp_leaves.date_to < supp_leaves.date_from:
                raise ValidationError(_("End date must be greater than start date!"))

    @api.constrains("date_from", "date_to")
    def _check_leave_duration(self):
        """
        Check for the Overlapping record.

        Raises:
            ValidationError: if an overlapping record is found.
        """
        for leave in self:
            domain = [
                ("date_from", "<=", leave.date_to),
                ("date_to", ">=", leave.date_from),
                ("partner_id", "=", leave.partner_id.id),
                ("id", "!=", leave.id),
            ]
            if self.search_count(domain):
                raise ValidationError(
                    _("You can not have 2 leaves that overlaps on same day!")
                )
