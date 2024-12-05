<template>
  <button class="btn btn-default" @click="link">Assign an existing bug</button>
</template>

<script>
import swal from "sweetalert";
import { defineComponent } from "vue";
import { assignExternalBug, errorParser } from "../../helpers";
import AssignBtnForm from "./AssignBtnForm.vue";

export default defineComponent({
  components: {
    AssignBtnForm,
  },
  props: {
    bucket: {
      type: Number,
      required: true,
    },
    providers: {
      type: Array,
      required: true,
    },
  },
  methods: {
    async link() {
      const formCtor = defineComponent(AssignBtnForm);
      const assignForm = new formCtor({
        parent: this,
        propsData: {
          providers: this.providers,
        },
      }).$mount();

      const value = await swal({
        title: "Assign External Bug",
        content: assignForm.$el,
        buttons: true,
      });

      if (value) {
        try {
          const data = await assignExternalBug(
            this.bucket,
            assignForm.provider,
            assignForm.bug,
          );
          window.location.href = data.url;
        } catch (err) {
          swal("Oops", errorParser(err), "error");
        }
      }
    },
  },
});
</script>
